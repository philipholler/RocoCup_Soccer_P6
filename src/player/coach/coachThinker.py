import queue
import threading
import time

from player import client_connection, strategy
from player.strategy import Objective


class CoachThinker(threading.Thread):
    def __init__(self, team_name: str):
        super().__init__()
        self.team = team_name
        # Connection with the server
        self.connection: client_connection.Connection = None
        # Non processed inputs from server
        self.input_queue = queue.Queue()
        self.current_objective: Objective = None

        self.strategy = strategy.Strategy()

        self.my_bool = True

    def start(self) -> None:
        super().start()

        init_string = "(init " + self.team + "(version 7))"
        self.connection.action_queue.put(init_string)

    def run(self) -> None:
        super().run()
        while True:
            self._think()

    def _think(self) -> None:
        time.sleep(1)
        print("Coach from team ({0}) thinking...".format(self.team))
        while not self.input_queue.empty():
            msg = self.input_queue.get()
            # print(msg)
            self.connection.action_queue.put("(look)")
