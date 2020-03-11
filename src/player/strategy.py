import player.player_state


class Strategy:
    def __init__(self, player_state) -> None:
        super().__init__()
        self.current_goal = "attack"
        self.player_state = player_state
