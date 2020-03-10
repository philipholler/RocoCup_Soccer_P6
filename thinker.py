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
        self.player_conn.send_message("(init " + self.player_state.team_name + ")")
        msg = self.player_conn.receive_message()
        parsing.parse_message_update_state(msg, self.player_state)

    def run(self) -> None:
        super().run()
        while True:
            self.think()

    def think(self):
        for msg in self.input_queue.get():
            if self.player_state.team_name == "Team1" and self.player_state.player_num == "1":
                print("Msg: ", msg)
        return
