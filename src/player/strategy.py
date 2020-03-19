import player.player
from player.thinker import Thinker, Objective
from player.world import Coordinate

_congo_positions = [Coordinate(-40, -15), Coordinate(40, -15), Coordinate(40, 15), Coordinate(-40, 15)]


class Strategy:
    def __init__(self, player_state, thinker: Thinker) -> None:
        super().__init__()
        self.current_goal = "attack"
        self.player_state = player_state
        self.congo_count = 0

    def determine_objective(self, player_state, thinker: Thinker):
        current_objective = thinker.current_objective
        if current_objective is None or current_objective.is_achieved():
            new_objective = Objective(lambda: thinker.jog_towards(_congo_positions[self.congo_count]),
                                      lambda: thinker.is_near(_congo_positions[self.congo_count]))
            self.congo_count += 1
            return new_objective
        return current_objective
