import queue
import re
import threading
import time

from client_connection import Connection


class FakeMonitorThinker(threading.Thread):

    def __init__(self, start_delay):
        super().__init__()
        self._stop_event = threading.Event()
        self.input_queue = queue.Queue()
        self.connection: Connection = None
        self.start_delay = start_delay
        self.start_time = time.time() + self.start_delay
        self.has_started_game = False
        self.current_tick = 0


    def start(self) -> None:
        super().start()
        self.connection.action_queue.put("(dispinit version 4)")

    def run(self) -> None:
        super().run()
        self.think()

    def think(self):
        while not self._stop_event.is_set():
            while not self.input_queue.empty():
                # Parse message and update player state / world view
                msg: str = self.input_queue.get()

                # Parse current tick
                if "(show" in msg:
                    tick = re.match(r'\(show ([0-9]*) \(.*', msg).group(1)
                    self.current_tick = int(tick)

                if self.current_tick == 3000:
                    time.sleep(5)
                    self.connection.action_queue.put("(dispstart)")


            if time.time() >= self.start_time:
                if not self.has_started_game:
                    self.has_started_game = True
                    self.connection.action_queue.put("(dispstart)")


    def stop(self) -> None:
        self._stop_event.set()