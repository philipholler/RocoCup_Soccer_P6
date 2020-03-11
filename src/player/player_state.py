class PlayerState:

    def __init__(self):
        self.side = ""
        self.team_name = ""
        self.player_num = ""
        self.game_state = ""
        self.sim_time = 0
        super().__init__()

    def __str__(self) -> str:
        return "side: {0}, team_name: {1}, player_num: {2}".format(self.side, self.team_name, self.player_num)


