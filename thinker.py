import player_state
import threading
import queue
import player_connection
import time
import re
import parsing
import random as r


class Thinker(threading.Thread):
    def __init__(self, team_name: str):
        super().__init__()
        self.player_state = player_state.PlayerState()
        self.player_state.team_name = team_name
        self.player_conn: player_connection.PlayerConnection = None
        self.action_queue = queue.Queue()
        self.input_queue = queue.Queue()

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
            msg = self.input_queue.get()
            parsing.parse_message_update_state(msg, self.player_state)
            if self.player_state.team_name == "Team1" and self.player_state.player_num == "1":
                parsing.approx_position(msg)
        if self.player_state.team_name == "Team1" and self.player_state.player_num == "1":
            self.player_conn.action_queue.put("(dash 50)")
        return

    def position_player(self):
        x = r.randint(-20, 20)
        y = r.randint(-20, 20)
        move_action = "(move " + str(x) + " " + str(y) + ")"
        self.player_conn.action_queue.put(move_action)