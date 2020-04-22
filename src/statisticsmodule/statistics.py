class Game:

    def __init__(self):
        self.gameID = ""
        self.teams = []
        self.ball = None


class Team:

    def __init__(self):
        self.side = ""
        self.name = ""
        self.goals = 0
        self.kicks = 0


class Ball:

    def __init__(self):
        self.x_coord = 0
        self.y_coord = 0
        self.delta_x = 0
        self.delta_y = 0