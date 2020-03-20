from player import thinker, client_connection
import threading


class Client(threading.Thread):

    # Start up the player
    def __init__(self, team: str, UDP_PORT, UDP_IP, player_type) -> None:
        # Init thinker thread
        super().__init__()
        self.think = thinker.Thinker(team, player_type)
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



