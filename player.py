import time

import parsing
import player_state
import player_connection
import keyboard


class Player:
    # Start up the player
    def __init__(self, team: str, UDP_PORT, UDP_IP) -> None:
        # Initialise state
        self.player_state: player_state.PlayerState = player_state.PlayerState()
        self.player_state.team_name = team

        # Establish connection with server. Use self.player_conn for all communication with the server.
        self.player_conn = player_connection.PlayerConnection(UDP_PORT=UDP_PORT, UDP_IP=UDP_IP)
        self.player_conn.connect_to_server(self.player_state)

        # Position player
        self.player_conn.send_message("(move -10 0)")

        # Start main logic loop for player
        self.__main_loop()

    """
    The interface of functions, like move_to(x,y) etc.
    """

    def move_on_home_ground(self, x_coord, y_coord):
        self.player_conn.send_message("(move -" + x_coord + " -" + y_coord + ")")

    def move_on_opponent_side(self, x_coord, y_coord):
        self.player_conn.send_message("(move " + x_coord + " " + y_coord + ")")

    def dash_to(self, end_coord, dash_power):
        # TODO find way to get coord of player
        while self.player_state.coord != end_coord:
            # TODO turn towards coord, "20" just placeholder
            turn_power = "20"
            self.player_conn.send_message("(turn " + turn_power + ")")
            self.player_conn.send_message("(dash " + dash_power + ")")

    def dash_towards_ball(self, ball_coord, dash_power):
        self.dash_to(ball_coord, dash_power)

    def dash_and_kick(self, ball_coord, dash_power, kick_power, kick_angle):
        self.dash_towards_ball(ball_coord, dash_power)
        self.player_conn.send_message("(kick " + kick_power + " " + kick_angle + ")")

    def pass_ball_to_player(self, kick_power, player_angle):
        self.player_conn.send_message("(kick " + kick_power + " " + player_angle + ")")

    def turn(self, moment):
        self.player_conn.send_message("(turn " + moment + " )")

    def catch_ball(self, direction):
        self.player_conn.send_message("(catch " + direction + " )")

    # def tackle_opponent(self, opponent):

    # def change_view(self, width, quality):

    # def say(self, message):
        # says message to others who can hear

    # def sense_body(self):
        # returns a lot of info about player

    # def score(self):
        # returns score

    # def turn_neck(self, angle):
        # turns neck separate from body

    # Add main functionality of player
    def __main_loop(self):
        while True:
            msg = self.player_conn.receive_message()
            while True:
                msg = self.player_conn.receive_message()
                if msg is None:
                    break
                self.__update_state(msg)

            time.sleep(0.05)  # Server tick rate 10 / second
            if self.player_state.player_num == "1" and self.player_state.team_name == "Team1":
                # self.player_conn.send_message("(turn 5)")
                # time.sleep(0.1)
                '''if keyboard.is_pressed('w'):
                    self.player_conn.send_message("(dash 50)")
                if keyboard.is_pressed('s'):
                    self.player_conn.send_message("(dash -50)")
                if keyboard.is_pressed('a'):
                    self.player_conn.send_message("(turn -20)")
                if keyboard.is_pressed('d'):
                    self.player_conn.send_message("(turn 20)")'''
            '''
            if msg is not None:
                self.__update_state(msg)
                if self.player_state.player_num == "1" and self.player_state.team_name == "Team1":
                    #self.player_conn.send_message("(turn 5)")
                    #time.sleep(0.1)
                    if keyboard.is_pressed('w'):
                        self.player_conn.send_message("(dash 50)")
                        print("dashing")
                    if keyboard.is_pressed('s'):
                        self.player_conn.send_message("(dash -50)")
                    if keyboard.is_pressed('a'):
                        self.player_conn.send_message("(turn -20)")
                    if keyboard.is_pressed('d'):
                        self.player_conn.send_message("(turn 20)")
                if self.player_state.player_num == "1" and self.player_state.team_name == "Team1":
                    parsing.approx_position(msg)
            '''

    def __update_state(self, msg: str):
        a = self.player_state  # YADA YADA
        if self.player_state.player_num == "1" and self.player_state.team_name == "Team1":
            parsing.approx_position(msg)
        return msg
