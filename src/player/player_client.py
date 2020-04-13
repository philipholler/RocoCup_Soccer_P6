from player import player_thinker
import client_connection
import threading
import time


class Client(threading.Thread):

    # Start up the player
    def __init__(self, team: str, UDP_PORT, UDP_IP, player_type) -> None:
        # Init thinker thread
        super().__init__()
        self._stop_event = threading.Event()
        self.think = player_thinker.Thinker(team, player_type)
        # Init player connection thread
        self.player_conn = client_connection.Connection(UDP_PORT=UDP_PORT, UDP_IP=UDP_IP, think=self.think)
        # Give reference of connection to thinker thread
        self.think.player_conn = self.player_conn

    def start(self) -> None:
        super().start()
        # Connect to server with team name from thinker
        self.player_conn.start()
        # Start thinking
        self.think.start()

    def run(self) -> None:
        super().run()
        while True:
            if self._stop_event.is_set():
                return
            time.sleep(0.1)

    def stop(self) -> None:
        self._stop_event.set()
        self.player_conn.stop()
        self.player_conn.join()
        self.think.stop()
        self.think.join()
