import threading
import queue

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
        self.last_action_time = 0
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
        can_perform_action = False
        while not self._stop_event.is_set():
            while not self.input_queue.empty():
                # Parse message and update player state / world view
                msg: str = self.input_queue.get()
                if msg.startswith("(see"):
                    can_perform_action = True
                parsing.parse_message_update_state(msg, self.player_state)

            if not self.is_positioned:
                self.position_player()
            # Update current objective in accordance to the player's strategy
            if can_perform_action: #
                self.current_objective = determine_objective(self.player_state, self.current_objective)
                action = self.current_objective.perform_action()
                if action is not None:
                    if isinstance(action, str):
                        self.player_conn.action_queue.put(action)
                    else:
                        for msg in action:
                            self.player_conn.action_queue.put(msg)
                can_perform_action = False

            time.sleep(0.01)

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
