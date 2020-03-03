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
        self.action_queue = Queue()

        # Setup connection with soccer_sim
        self.player_connection = player_connection.PlayerConnection(UDP_PORT, UDP_IP, self.player_state)
        init_player_msg: str = "(init " + team + ")"
        self.player_connection_thread = threading.Thread(target=lambda:self.player_connection.connect_to_server())
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
            self.player_connection.request_action("(dash 60)")
