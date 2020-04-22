from random import choice

import parsing
from player import actions
from player.player import PlayerState
from player.world_objects import Coordinate

""" Starting positions
Forsvarskæde: (-36, 10), (-36, 20), (-36, -10), (-36, -20)
Midtbane: (-23 10), (-23, 20), (-23, -10), (-23, -20)
Angreb: (-9, 10), (-9, -10)
Målmand: (-50, 0)
"""

starting_player_pos = [[]] * 2
starting_player_pos[1] = [(50, 0), (-36, 10), (-36, 20), (-36, -10), (-36, -20), (-23, 10), (-23, 20), (-23, -10),
                          (-23, -20), (-9, 10), (-9, -10)]
# Inverse x-positions for team 2
starting_player_pos[0] = list(map(lambda c: (-c[0], c[1]), starting_player_pos[1]))


class Objective:
    def __init__(self, action_to_perform, achievement_criteria) -> None:
        self.achievement_criteria = achievement_criteria
        self.perform_action = action_to_perform

    def is_achieved(self):
        return self.achievement_criteria()

    def perform_action(self):
        self.perform_action()


def determine_objective(state: PlayerState, current_objective: Objective):
    if current_objective is not None and not current_objective.is_achieved():
        return current_objective

    if state.is_near_ball():
        pass_target = _find_pass_target(state)
        if pass_target is None:
            return orient_objective(state)

        return Objective(lambda: actions.pass_ball_to(pass_target, state),
                         lambda: not state.is_near_ball())

    # If less than 15 meters from ball attempt to retrieve it
    if state.world_view.game_state == 'play_on':
        if state.is_near_ball(10.0):
            return Objective(lambda: actions.jog_towards_ball(state),
                             lambda: state.is_near_ball())

    if state.team_name == "Team1":
        target_position = starting_player_pos[0][state.num - 1]
    else:
        target_position = starting_player_pos[1][state.num - 1]
    target_position = Coordinate(target_position[0], target_position[1])

    if state.is_near(target_position):
        new_objective = orient_objective(state)
    else:
        new_objective = Objective(lambda: actions.jog_towards(state, target_position),
                                  lambda: True)  # Always interruptable

    return new_objective


def orient_objective(state: PlayerState):
    return Objective(lambda: actions.orient_self(state), lambda: True)


def _find_pass_target(state: PlayerState):
    if state.coach_command.is_value_known(state.now() - 7 * 10):
        coach_command = state.coach_command.get_value()
        if "pass" in coach_command:
            pass_pairs = parsing.parse_pass_command(coach_command)

            for pair in pass_pairs:
                if state.num == pair[0]:
                    return pair[1]

    team_members = state.world_view.get_teammates(state.team_name, max_data_age=4)
    if len(team_members) is 0:
        return None
    return choice(team_members).num
