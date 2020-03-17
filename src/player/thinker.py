import threading
import queue
from player import player_connection, player_state
import time
import parsing
import random as r
import player.strategy as strategy


class Thinker(threading.Thread):
    def __init__(self, team_name: str):
        super().__init__()
        self.player_state = player_state.PlayerState()
        self.player_state.team_name = team_name
        # Connection with the server
        self.player_conn: player_connection.PlayerConnection = None
        # Queue for actions to be send
        self.action_queue = queue.Queue()
        # Non processed inputs from server
        self.input_queue = queue.Queue()

        self.strategy = strategy.Strategy(self.player_state)

        self.my_bool = True

    def start(self) -> None:
        super().start()
        init_string = "(init " + self.player_state.team_name + ")"
        self.player_conn.action_queue.put(init_string)
        self.position_player()

    def run(self) -> None:
        super().run()
        while True:
            self.think()

    def think(self):
        time.sleep(0.1)
        while not self.input_queue.empty():
            # Parse message and update player state / world view
            msg = self.input_queue.get()
            parsing.parse_message_update_state(msg, self.player_state)
            # Give the strategy a new state
            self.strategy.player_state = self.player_state

        if self.player_state.team_name == "Team1" and self.player_state.player_num == "1":
            if self.my_bool:
                self.player_conn.action_queue.put("(dash 100)")
                self.player_conn.action_queue.put("(turn -20)")
                self.my_bool = False
            else:
                self.player_conn.action_queue.put("(turn 20)")
                self.player_conn.action_queue.put("(turn_neck 20)")
                self.my_bool = True
        else:
            dash_rate = r.randint(-50, 50)
            self.player_conn.action_queue.put("(dash " + str(dash_rate) + ")")
            turn_rate = r.randint(-5, 5)
            self.player_conn.action_queue.put("(turn_neck " + str(turn_rate) + ")")
        return

    def position_player(self):
        x = r.randint(-20, 20)
        y = r.randint(-20, 20)
        move_action = "(move " + str(x) + " " + str(y) + ")"
        self.player_conn.action_queue.put(move_action)
