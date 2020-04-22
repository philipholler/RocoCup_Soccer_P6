import queue
import threading
import time
import parsing
from coaches.world_objects_coach import WorldViewCoach

import client_connection
from uppaal import strategy


class CoachThinker(threading.Thread):
    def __init__(self, team_name: str):
        super().__init__()
        self._stop_event = threading.Event()
        self.world_view = WorldViewCoach(0, team_name)
        self.team = team_name
        # Connection with the server
        self.connection: client_connection.Connection = None
        # Non processed inputs from server
        self.input_queue = queue.Queue()


    def start(self) -> None:
        super().start()

        # (init TEAMNAME (version VERSION))
        init_string = "(init " + self.team + " (version 16))"
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
            parsing.parse_message_online_coach(msg, self.team, self.world_view)

        self.update_strategy()

        # USE THIS FOR SENDING MESSAGES TO PLAYERS
        # self.connection.action_queue.put('(say (freeform "MSG"))')

    def stop(self) -> None:
        self._stop_event.set()

    def update_strategy(self):
        strat = strategy.generate_strategy(self.world_view)
        if strat is not None:
            self.say(' '.join(strat))

    def say(self, msg):
        self.connection.action_queue.put('(say (freeform "{0}"))'.format(msg, self.world_view.sim_time))