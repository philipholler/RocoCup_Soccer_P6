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
from player.world import Coordinate


class Thinker(threading.Thread):
    def __init__(self, team_name: str, player_type: str):
        super().__init__()
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
        time.sleep(0.5)
        self.position_player()
        while True:
            self.think()

    def think(self):
        time.sleep(0.1)
        while not self.input_queue.empty():
            # Parse message and update player state / world view
            msg = self.input_queue.get()
            parsing.parse_message_update_state(msg, self.player_state)

        # Update current objective in accordance to the player's strategy
        if self.player_state.player_num == 1 and self.player_state.team_name == "Team1":
            self.current_objective = self.strategy.determine_objective(self.player_state, self.current_objective)
            action = self.current_objective.perform_action()
            self.player_conn.action_queue.put(action)

        return

    def position_player(self):
        x = r.randint(-20, 20)
        y = r.randint(-20, 20)
        move_action = "(move " + str(x) + " " + str(y) + ")"
        if self.player_state.team_name == "Team1" and self.player_state.player_num == 2:
            move_action = "(move -5 -5)"
        if self.player_state.player_type == "goalie":
            move_action = "(move -50 0)"
        self.player_conn.action_queue.put(move_action)

