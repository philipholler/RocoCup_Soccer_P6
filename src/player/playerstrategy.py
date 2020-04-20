from player import actions
from player.player import PlayerState
from player.world_objects import Coordinate


_conga_positions = [Coordinate(-35, -20), Coordinate(35, -20), Coordinate(35, 20), Coordinate(-35, 20)]

_player_positions = [(6, 10), (10, 22), (26, 18), (32, 18), (26, 12)]
_opponent_positions = [(16, 20), (28, 18), (25, 0), (28, 18), (14, 22)]


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

    def determine_objective(self, player_state : PlayerState, current_objective: Objective):
        if current_objective is None or current_objective.is_achieved():

            if player_state.team_name == "Team1":
                target_position = _player_positions[player_state.num - 1]
            else:
                target_position = _opponent_positions[player_state.num - 1]
            target_position = Coordinate(target_position[0], target_position[1])

            if player_state.num == 1 and player_state.team_name == "Team1":
                if player_state.is_near_ball():
                    new_objective = Objective(lambda: None,
                                              lambda: False)
                else:
                    new_objective = Objective(lambda: actions.jog_towards_ball(player_state),
                                              lambda: player_state.is_near_ball())
            elif player_state.is_near(target_position):
                new_objective = Objective(lambda: None,
                                          lambda: False)
            else:
                new_objective = Objective(lambda: actions.jog_towards(player_state, target_position),
                                          lambda: player_state.is_near(target_position))

            return new_objective
        return current_objective
