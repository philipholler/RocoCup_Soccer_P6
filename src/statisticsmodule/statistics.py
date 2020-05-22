import math

from geometry import Coordinate


class Game:

    def __init__(self):
        self.last_kicker = Player()
        self.last_kicker_tick = 0
        self.goals = []
        self.gameID = ""
        self.teams = []
        self.fieldprogress = 0
        self.player_l_stamina_under = []
        self.player_l_stamina_over = []
        self.player_r_stamina_under = []
        self.player_r_stamina_over = []
        self.kick_dict = {}
        self.real_kick_dict = {}
        self.biptest_dict = {}
        self.possession_l_in_ticks = 0
        self.possession_r_in_ticks = 0

        # For use in the goalie positioning statistics
        self.ball_first_time_outside_field = None

        # The stage at tick 40, is in place 40 in the array
        self.show_time = []


class Team:

    def __init__(self):
        self.side = ""
        self.name = ""
        self.goals = 0
        self.stamina_under = 0
        self.stamina_over = 0
        self.number_of_players = 0


class Stage:

    def __init__(self):
        self.ball = Ball()
        self.players = []
        self.team_l_kicks = 0
        self.team_r_kicks = 0
        self.team_l_real_kicks = 0
        self.team_r_real_kicks = 0
        self.goalies = []

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

    def is_ball_outside_field(self):
        if self.ball.x_coord < -52.5 or 52.5 < self.ball.x_coord:
            return True
        if self.ball.y_coord < -34 or 34 < self.ball.y_coord:
            return True
        return False

    def get_ball_coord(self) -> Coordinate:
        return Coordinate(self.ball.x_coord, self.ball.y_coord)

class Ball:

    def __init__(self):
        self.x_coord = 0
        self.y_coord = 0
        self.delta_x = 0
        self.delta_y = 0

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
        self.stamina = 0
        self.stamina_under = 0
        self.stamina_over = 0

    def print_player(self):
        print("player side: " + self.side + " no: " + str(self.no) +
              " player coords: " + str(self.x_coord) + " " + str(self.y_coord) + "kick count: " + str(self.kicks))
