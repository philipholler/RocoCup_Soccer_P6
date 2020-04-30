import math
import re
import threading
import queue

from constants import PLAYER_SPEED_DECAY
from geometry import calculate_full_origin_angle_radians
from player import player
import client_connection
from player.playerstrategy import Objective
import time
import parsing
from player.playerstrategy import determine_objective
from player.startup_positions import goalie_pos, defenders_pos, midfielders_pos, strikers_pos
from player.world_objects import Coordinate


class Thinker(threading.Thread):

    def __init__(self, team_name: str, player_type: str):
        super().__init__()
        self._stop_event = threading.Event()
        self.player_state = player.PlayerState()
        self.player_state.team_name = team_name
        self.player_state.player_type = player_type
        # Connection with the server
        self.player_conn: client_connection.Connection = None
        # Non processed inputs from server
        self.input_queue = queue.Queue()
        self.current_objective: Objective = None
        self.is_positioned = False

    def start(self) -> None:
        super().start()
        if self.player_state.player_type == "goalie":
            init_string = "(init " + self.player_state.team_name + "(goalie)" + "(version 16))"
        else:
            init_string = "(init " + self.player_state.team_name + " (version 16))"
        self.player_conn.action_queue.put(init_string)

    def run(self) -> None:
        super().run()
        # Wait for client connection thread to receive the correct new port
        time.sleep(1.5)
        # Set accepted coach language versions
        self.player_conn.action_queue.put("(clang (ver 8 8))")
        self.think()

    def stop(self) -> None:
        self._stop_event.set()

    def think(self):
        self.current_objective = determine_objective(self.player_state)
        time_since_last_tick = 0
        last_measured_time = time.time()
        can_send = False
        while not self._stop_event.is_set():

            while not self.input_queue.empty():
                # Parse message and update player state / world view
                msg: str = self.input_queue.get()
                if msg.startswith("(sense_body"):
                    can_send = True
                parsing.parse_message_update_state(msg, self.player_state)

            if not self.is_positioned:
                self.position_player()

            # Update current objective in accordance to the player's strategy
            if can_send:
                self.perform_action()
                can_send = False

            time.sleep(0.05)

    # Called every 100ms
    def perform_action(self):
        if not self.current_objective.has_next_actions(self.player_state):
            self.current_objective = determine_objective(self.player_state)
        commands = self.current_objective.get_next_commands(self.player_state)
        # print("Time : ", self.player_state.now(), " | position = ", self.player_state.position.get_value(), " | Speed: ", self.player_state.body_state.speed, " | Executing commands", commands)
        rotation = calculate_full_origin_angle_radians(Coordinate(-36, -20), self.player_state.position.get_value())
        rotation = math.degrees(rotation)
        rotation -= self.player_state.body_angle.get_value()
        dist = Coordinate(-36, -20).euclidean_distance_from(self.player_state.position.get_value())
        print("Angle to target : ", rotation, " | Distance: ", dist)
        print("Executing : ", commands)
        for command in commands:
            if command is not None:
                self.player_conn.action_queue.put(command)

    def position_player(self):
        if (len(goalie_pos) + len(defenders_pos) + len(midfielders_pos) + len(strikers_pos)) > 11:
            raise Exception("Too many startup positions given. Expected < 12, got: " + str(len(goalie_pos)
                                                                                           + len(defenders_pos)
                                                                                           + len(midfielders_pos)
                                                                                           + len(strikers_pos)))

        self.assign_position()
        if self.player_state.player_type == "goalie":
            if len(goalie_pos) > 1:
                raise Exception("Only 1 goalie / goalie position allowed")
            pos = goalie_pos[0]
            move_action = "(move {0} {1})".format(pos[0], pos[1])
            self.player_state.playing_position = Coordinate(pos[0], pos[1])
        elif self.player_state.player_type == "defender":
            index = self.player_state.num - 1 - len(goalie_pos)
            pos = defenders_pos[index]
            self.player_state.playing_position = Coordinate(pos[0], pos[1])
            move_action = "(move {0} {1})".format(pos[0], pos[1])
        elif self.player_state.player_type == "midfield":
            index = self.player_state.num - 1 - len(goalie_pos) - len(defenders_pos)
            pos = midfielders_pos[index]
            self.player_state.playing_position = Coordinate(pos[0] + 10, pos[1])
            move_action = "(move {0} {1})".format(pos[0], pos[1])
        elif self.player_state.player_type == "striker":
            index = self.player_state.num - 1 - len(goalie_pos) - len(defenders_pos) - len(midfielders_pos)
            pos = strikers_pos[index]
            self.player_state.playing_position = Coordinate(pos[0] + 10, pos[1])
            move_action = "(move {0} {1})".format(pos[0], pos[1])
        else:
            raise Exception("Could not position player: " + str(self.player_state))
        self.player_state.starting_position = Coordinate(pos[0], pos[1])
        self.player_conn.action_queue.put(move_action)
        self.is_positioned = True

    def assign_position(self):
        if self.player_state.num == 1:
            if self.player_state.player_type != "goalie":
                raise Exception("Goalie is not player num 1")
            else:
                return
        if 1 < self.player_state.num <= 1 + len(defenders_pos):
            self.player_state.player_type = "defender"
        elif 1 + len(defenders_pos) < self.player_state.num <= 1 + len(defenders_pos) + len(midfielders_pos):
            self.player_state.player_type = "midfield"
        elif 1 + len(defenders_pos) + len(midfielders_pos) < self.player_state.num <= 1 + len(defenders_pos) \
                + len(midfielders_pos) + len(strikers_pos):
            self.player_state.player_type = "striker"
        else:
            raise Exception("Could not assign position. Unum unknown. Expected unum between 1-11, got: "
                            + str(self.player_state.num) + " for player " + str(self.player_state))
