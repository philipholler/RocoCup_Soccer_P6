from player import actions
from player.world import Coordinate


_conga_positions = [Coordinate(-35, -20), Coordinate(35, -20), Coordinate(35, 20), Coordinate(-35, 20)]


class Objective:

    def __init__(self, action_to_perform, achievement_criteria) -> None:
        self.achievement_criteria = achievement_criteria
        self.perform_action = action_to_perform

    def is_achieved(self):
        return self.achievement_criteria()

    def perform_action(self):
        self.perform_action()


class Strategy:
    def __init__(self) -> None:
        super().__init__()
        self.conga_count = -1

    def determine_objective(self, player_state, current_objective: Objective):
        if current_objective is None or current_objective.is_achieved():
            self.conga_count += 1
            self.conga_count %= 4
            new_objective = Objective(lambda: actions.jog_towards(player_state, _conga_positions[self.conga_count]),
                                      lambda: player_state.is_near(_conga_positions[self.conga_count]))
            return new_objective
        return current_objective
