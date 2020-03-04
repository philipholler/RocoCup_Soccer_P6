import time

import player_state
import player_connection


class Player:

    # Start up the player
    def __init__(self, team: str, UDP_PORT, UDP_IP) -> None:
        # Initialise state
        self.player_state: player_state.PlayerState = player_state.PlayerState()
        self.player_state.team_name = team

        self.player_conn = player_connection.PlayerConnection(UDP_PORT=UDP_PORT, UDP_IP=UDP_IP)
        self.player_conn.connect_to_server(self.player_state)

        self.__main_loop()

    """
    The interface of functions, like move_to(x,y) etc.
    """

    def __function_a(self):
        return

    def __function_b(self):
        return

    def __main_loop(self):
        while True:
            msg = self.player_conn.receive_message()
            if msg is not None:
                self.__update_state(msg)
                if self.player_state.player_num == "1" and self.player_state.team_name == "Team1":
                    self.player_conn.send_message("(dash 50)")
                    print(msg)

    def __update_state(self, msg: str):
        a = self.player_state  # YADA YADA
        return msg
