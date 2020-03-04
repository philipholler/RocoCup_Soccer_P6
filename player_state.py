class PlayerState:

    def __init__(self):
        self.side = ""
        self.team_name = ""
        self.player_num = ""
        super().__init__()

    def __str__(self) -> str:
        return "side: {0}, team_name: {1}, player_num: {2}".format(self.side, self.team_name, self.player_num)


