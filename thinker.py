import player_state
import threading
import queue
import player_connection
import time
import re
import parsing


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
        self.player_conn.action_queue.put("(move -10 -10)")

    def run(self) -> None:
        super().run()
        while True:
            self.think()

    def think(self):
        my_string: str = ""
        while self.input_queue.not_empty:
            char = self.input_queue.get()
            my_string = my_string + str(char)
        if my_string != "":
            parsing.parse_message_update_state(my_string, self.player_state)
        if self.player_state.team_name == "Team1" and self.player_state.player_num == "1":
            print("Hej")
        return
