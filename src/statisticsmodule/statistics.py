class Game:

    def __init__(self):
        self.gameID = ""
        self.teams = []

        # The stage at tick 40, is in place 40 in the array
        self.show_time = []


class Team:

    def __init__(self):
        self.side = ""
        self.name = ""
        self.goals = 0
        self.kicks = 0


class Stage:

    def __init__(self):
        self.ball = Ball()
        self.players = []

    def print_stage(self):
        self.ball.print_ball()

        for player in self.players:
            player.print_player()


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

    def print_player(self):
        print("player side: " + self.side + " no: " + str(self.no) +
              " player coords: " + str(self.x_coord) + " " + str(self.y_coord))


