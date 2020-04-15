from player import actions
from player.world_objects import Coordinate


_conga_positions = [Coordinate(-35, -20), Coordinate(35, -20), Coordinate(35, 20), Coordinate(-35, 20)]


class Objective:

    def __init__(self, action_to_perform, achievement_criteria) -> None:
        self.achievement_criteria = achievement_criteria
        self.perform_action = action_to_perform

    def is_achieved(self):
        return self.achievement_criteria()

    def perform_action(self):
        self.perform_action()


class PlayerStrategy:
    def __init__(self) -> None:
        super().__init__()
        self.conga_count = -1

    def determine_objective(self, player_state, current_objective: Objective):
        if current_objective is None or current_objective.is_achieved():
            if player_state.is_near_ball():
                new_objective = Objective(lambda: actions.kick_to_goal(player_state),
                                          lambda: not player_state.is_near_ball())
                pass
            else:
                self.conga_count += 1
                self.conga_count %= 4
                new_objective = Objective(lambda: actions.jog_towards_ball(player_state),
                                          lambda: player_state.is_near_ball())

            return new_objective
        return current_objective
