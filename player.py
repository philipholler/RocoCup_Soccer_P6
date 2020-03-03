import threading
from queue import Queue

import player_state
import player_connection


class Player:

    # Start up the player
    def __init__(self, team: str, UDP_PORT, UDP_IP) -> None:
        # Initialise state
        self.player_state: player_state.PlayerState = player_state.PlayerState()
        self.player_state.team_name = team

        # Action queue
        action_queue = Queue()

        # Setup connection with soccer_sim
        self.player_connection = player_connection.PlayerConnection(UDP_PORT, UDP_IP, self.player_state, self.action_queue)
        init_player_msg: str = "(init " + team + ")"
        self.player_connection_thread = threading.Thread(target=self.player_connection.connect_to_server())
        self.player_connection_thread.start()

        # Start main reaction loop
        self.main_loop()

    """
    The interface of functions, like move_to(x,y) etc.
    """

    def function_a(self):
        return

    def function_b(self):
        return

    # Add main functionality of player
    def main_loop(self):
        while True:
            self.action_queue.put("(dash 50)")
