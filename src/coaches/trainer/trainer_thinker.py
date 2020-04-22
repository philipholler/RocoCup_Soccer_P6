import queue
import threading
import time
from random import random, randint

import client_connection
import parsing
from coaches.world_objects_coach import WorldViewCoach


class TrainerThinker(threading.Thread):
    def __init__(self):
        super().__init__()
        self._stop_event = threading.Event()
        self.team = "TRAINER"
        self.world_view = WorldViewCoach(0, self.team)
        # Connection with the server
        self.connection: client_connection.Connection = None
        # Non processed inputs from server
        self.input_queue = queue.Queue()


    def start(self) -> None:
        super().start()

        # (init (version VERSION))
        init_string = "(init (version 16))"
        self.connection.action_queue.put(init_string)

        time.sleep(1)

        # Enable periodic messages from the server with positions of all objects
        self.connection.action_queue.put("(eye on)")

    def run(self) -> None:
        super().run()
        while True:
            if self._stop_event.is_set():
                return
            self._think()

    def _think(self) -> None:
        time.sleep(0.1)
        while not self.input_queue.empty():
            msg: str = self.input_queue.get()
            parsing.parse_message_trainer(msg, self.world_view)

        x = randint(-20, 20)
        y = randint(-20, 20)

        command = "(move (ball) {0} {1} 0 0 0)".format(x, y)
        self.say_command(command)

    def stop(self) -> None:
        self._stop_event.set()

    def say_command(self, cmd):
        self.connection.action_queue.put(cmd)