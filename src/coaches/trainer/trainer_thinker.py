import queue
import threading
import time
from random import random, randint

import client_connection
import parsing
from coaches.world_objects_coach import WorldViewCoach
from coaches.trainer.scenarios import passing_strat


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
        self.is_scenario_set = False

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
        time.sleep(4)
        while True:
            if self._stop_event.is_set():
                return
            self._think()

    def _think(self) -> None:
        time.sleep(0.1)
        while not self.input_queue.empty():
            msg: str = self.input_queue.get()
            parsing.parse_message_trainer(msg, self.world_view)

        if not self.is_scenario_set:
            for msg in passing_strat:
                self.say_command(msg)
            self.is_scenario_set = True


    def stop(self) -> None:
        self._stop_event.set()

    def say_command(self, cmd):
        '''
        Example commands:
        (move (ball) -47 -9.16 0 0 0)   ---   (move (ball) *x* *y* *direction* *delta_x* *delta_y*)
        (move (player Team1 4) {0} {1} 0 0 0))   ---  (move (player *team* *unum*) *x* *y* *direction* *delta_x* *delta_y*)
        :param cmd: Command to send to server
        '''
        self.connection.action_queue.put(cmd)
