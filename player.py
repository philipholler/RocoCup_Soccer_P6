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

    def move_on_home_ground(self, x_coord, y_coord):
        self.player_connection.__send_message("(move -" + x_coord + " -" + y_coord + ")")

    def move_on_opponent_side(self, x_coord, y_coord):
        self.player_connection.__send_message("(move " + x_coord + " " + y_coord + ")")

    def dash_to(self, end_coord, dash_power):
        # TODO find way to get coord of player
        while self.player_state.coord != end_coord:
            # TODO turn towards coord, "20" just placeholder
            turn_power = "20"
            self.player_connection.__send_message("(turn " + turn_power + ")")
            self.player_connection.__send_message("(dash " + dash_power + ")")

    def dash_towards_ball(self, ball_coord, dash_power):
        self.dash_to(ball_coord, dash_power)

    def dash_and_kick(self, ball_coord, dash_power, kick_power, kick_angle):
        self.dash_towards_ball(ball_coord, dash_power)
        self.player_connection.__send_message("(kick " + kick_power + " " + kick_angle + ")")

    def pass_ball_to_player(self, kick_power, player_angle):
        self.player_connection.__send_message("(kick " + kick_power + " " + player_angle + ")")

    # def tackle_opponent(self, opponent):

    # Add main functionality of player
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
