import queue
import threading
import time

import client_connection
from coaches.world_objects_coach import WorldViewCoach
from coaches.trainer.trainer_thinker import TrainerThinker


class Trainer(threading.Thread):

    # Start up the player
    def __init__(self, UDP_PORT, UDP_IP) -> None:
        super().__init__()
        self._stop_event = threading.Event()
        self.think: TrainerThinker = TrainerThinker()
        # Init player connection thread
        self.connection = client_connection.Connection(UDP_PORT=UDP_PORT, UDP_IP=UDP_IP, think=self.think)
        # Give reference of connection to thinker thread
        self.think.connection = self.connection

    def start(self) -> None:
        super().start()
        # Connect to server with team name from thinker
        self.connection.start()
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
        self.connection.stop()
        self.connection.join()
        self.think.stop()
        self.think.join()