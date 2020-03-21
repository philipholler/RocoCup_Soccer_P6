from player import client_connection
from player.coach.coachThinker import CoachThinker
import threading


class Coach(threading.Thread):

    # Start up the player
    def __init__(self, team: str, UDP_PORT, UDP_IP) -> None:
        # Init thinker thread
        super().__init__()
        self.think: CoachThinker = CoachThinker(team_name=team)
        # Init player connection thread
        self.coach_conn = client_connection.Connection(UDP_PORT=UDP_PORT, UDP_IP=UDP_IP, think=self.think)
        # Give reference of connection to thinker thread
        self.think.connection = self.coach_conn

    def start(self) -> None:
        super().start()
        # Connect to server with team name from thinker
        self.coach_conn.start()
        # Start thinking
        self.think.start()

    def run(self) -> None:
        super().run()
