import enum
import threading
import queue

from geometry import calculate_smallest_origin_angle_between
from player import player, client_connection
from player.strategy import Objective
import time
import parsing
import random as r
import player.strategy as strategy


class Thinker(threading.Thread):

    def __init__(self, team_name: str, player_type: str):
        super().__init__()
        self._stop_event = threading.Event()
        self.player_state = player.PlayerState()
        self.player_state.team_name = team_name
        self.player_state.player_type = player_type
        # Connection with the server
        self.player_conn: client_connection.Connection = None
        # Queue for actions to be send
        self.action_queue = queue.Queue()
        # Non processed inputs from server
        self.input_queue = queue.Queue()
        self.current_objective: Objective = None
        self.last_action_time = 0

        self.strategy = strategy.Strategy()

        self.my_bool = True

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
        time.sleep(1)
        self.position_player()
        time.sleep(0.5)
        self.think()

    def stop(self) -> None:
        self._stop_event.set()

    def think(self):
        can_perform_action = False
        while not self._stop_event.is_set():
            while not self.input_queue.empty():
                # Parse message and update player state / world view
                msg : str = self.input_queue.get()
                if msg.startswith("(sense_body"):
                    can_perform_action = True
                parsing.parse_message_update_state(msg, self.player_state)

            # Update current objective in accordance to the player's strategy
            if can_perform_action and self.player_state.player_num == 1 and self.player_state.team_name == "Team1":
                self.current_objective = self.strategy.determine_objective(self.player_state, self.current_objective)
                action = self.current_objective.perform_action()
                if action is not None:
                    self.player_conn.action_queue.put(action)
                can_perform_action = False
                print(action)

            time.sleep(0.01)

    def position_player(self):
        x = r.randint(-20, 20)
        y = r.randint(-20, 20)
        move_action = "(move " + str(x) + " " + str(y) + ")"
        if self.player_state.team_name == "Team1" and self.player_state.player_num == 2:
            move_action = "(move -5 -5)"
        if self.player_state.player_type == "goalie":
            move_action = "(move -50 0)"
        if self.player_state.player_num == 10:
            move_action = "(move 0 0)"
        self.player_conn.action_queue.put(move_action)

