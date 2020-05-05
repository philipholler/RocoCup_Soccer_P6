import math

class Game:

    def __init__(self):
        self.last_kicker = Player()
        self.goals = []
        self.gameID = ""
        self.teams = []
        self.possession_length = 0

        # The stage at tick 40, is in place 40 in the array
        self.show_time = []


class Team:

    def __init__(self):
        self.side = ""
        self.name = ""
        self.goals = 0


class Stage:

    def __init__(self):
        self.ball = Ball()
        self.players = []
        self.team_l_kicks = 0
        self.team_r_kicks = 0

    def print_stage(self):

        print("team l kicks: " + str(self.team_l_kicks) + "\nteam r kicks: " + str(self.team_r_kicks))

        self.ball.print_ball()

        for player in self.players:
            player.print_player()

    def closest_player_team(self):
        closest_player = self.players[0]

        for player in self.players:
            if closest_player.distance_to_ball > player.distance_to_ball:
                closest_player = player

        return closest_player.side


class Ball:

    def __init__(self):
        self.x_coord = 0
        self.y_coord = 0
        self.delta_x = 0
        self.delta_y = 0
        self.abs_delta = 0

    def print_ball(self):
        print("ball coords:" + str(self.y_coord) + " " + str(self.y_coord) +
              "\nball deltas: " + str(self.delta_x) + " " + str(self.delta_y))



class Player:

    def __init__(self):
        self.side = ""
        self.no = 0
        self.x_coord = 0
        self.y_coord = 0
        self.kicks = 0
        self.distance_to_ball = 1000

    def print_player(self):
        print("player side: " + self.side + " no: " + str(self.no) +
              " player coords: " + str(self.x_coord) + " " + str(self.y_coord) + "kick count: " + str(self.kicks))
