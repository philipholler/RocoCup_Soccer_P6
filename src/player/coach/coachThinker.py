import queue
import threading
import time
import parsing

from player import client_connection, strategy
from player.strategy import Objective
from player.player import WorldView, PlayerState


class CoachThinker(threading.Thread):
    def __init__(self, team_name: str):
        super().__init__()
        self.world_view = WorldView(0)
        self.team = team_name
        # Connection with the server
        self.connection: client_connection.Connection = None
        # Non processed inputs from server
        self.input_queue = queue.Queue()
        self.current_objective: Objective = None

        self.strategy = strategy.Strategy()

    def start(self) -> None:
        super().start()

        # (init TEAMNAME (version VERSION))
        init_string = "(init " + self.team + " (version 16))"
        self.connection.action_queue.put(init_string)

        time.sleep(1)


    def run(self) -> None:
        super().run()
        while True:
            self._think()

    def _think(self) -> None:
        time.sleep(0.1)
        # Look command returns a vision of the entire field
        self.connection.action_queue.put("(look)")
        while not self.input_queue.empty():
            msg: str = self.input_queue.get()
            if msg.startswith("(error"):
                print("Coach for team {0} received error: {1}".format(self.team, msg))
            self.world_view = parsing.parse_message_online_coach(msg)


