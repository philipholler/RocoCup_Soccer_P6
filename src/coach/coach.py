import client_connection
import threading
import time

from coach.coachThinker import CoachThinker


class Coach(threading.Thread):

    # Start up the player
    def __init__(self, team: str, UDP_PORT, UDP_IP) -> None:
        # Init thinker thread
        super().__init__()
        self._stop_event = threading.Event()
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
        while True:
            if self._stop_event.is_set():
                return
            time.sleep(0.1)

    def stop(self) -> None:
        self._stop_event.set()
        self.coach_conn.stop()
        self.coach_conn.join()
        self.think.stop()
        self.think.join()