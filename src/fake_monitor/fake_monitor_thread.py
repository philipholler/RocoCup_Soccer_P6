import threading
import time

import client_connection
from fake_monitor.fake_monitor_thinker import FakeMonitorThinker

"""
This thread is created to pretend to be a fake monitor in order to disable graphics for robocut, 
while still receiving information about the game state, that the monitor normally uses.
This was used for debugging and tests purposes.
"""

class FakeMonitorClient(threading.Thread):

    def __init__(self, start_time: int, UDP_IP, UDP_PORT):
        super().__init__()
        self._stop_event = threading.Event()
        self.start_time = start_time
        self.thinker = FakeMonitorThinker(start_time)
        self.connection = client_connection.Connection(UDP_IP, UDP_PORT, self.thinker, should_print=False)
        self.thinker.connection = self.connection


    def start(self) -> None:
        super().start()
        self.connection.start()
        self.thinker.start()


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
        self.thinker.stop()
        self.thinker.join()