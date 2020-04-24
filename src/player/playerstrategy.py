from random import choice

import parsing
from player import actions
from player.player import PlayerState
from player.world_objects import Coordinate


class Objective:
    def __init__(self, action_planner, time_out) -> None:
        self.time_out = time_out
        self.action_planner = action_planner

    def should_recalculate(self):
        self.time_out -= 1
        return self.time_out <= 0

    def plan_actions(self):
        return self.action_planner()


def determine_objective(state: PlayerState, current_objective: Objective):
    if current_objective is not None and not current_objective.should_recalculate():
        return current_objective

    if state.is_near_ball(actions.MAXIMUM_KICK_DISTANCE):
        pass_target = _find_pass_target(state)
        if pass_target is None:
            return orient_objective(state)

        return Objective(lambda: actions.pass_ball_to(pass_target, state), time_out=1)

    # If less than 15 meters from ball attempt to retrieve it
    if state.world_view.game_state == 'play_on' and state.world_view.ball.is_value_known(state.now() - 5):
        if state.is_nearest_ball(2):
            return Objective(lambda: actions.jog_towards_ball(state), time_out=5)

    target_position = state.get_global_play_pos()

    if state.is_near(target_position):
        new_objective = orient_objective(state)
    else:
        new_objective = Objective(lambda: actions.jog_towards(state, target_position),
                                  time_out=1)  # Always interruptable

    return new_objective


def orient_objective(state: PlayerState):
    return Objective(lambda: actions.orient_self(state),  time_out=5)


def find_player(state, player_num):
    team_players = state.world_view.get_teammates(state.team_name, max_data_age=4)
    for p in team_players:
        if p.num is not None and int(p.num) == int(player_num):
            return p
    return None


def _find_pass_target(state: PlayerState):
    if state.coach_command.is_value_known(state.now() - 7 * 10):
        coach_command = state.coach_command.get_value()
        if "pass" in coach_command:
            pass_pairs = parsing.parse_pass_command(coach_command)

            for from_player, to_player in pass_pairs:
                if state.num == from_player:
                    return find_player(state, to_player)

    team_members = state.world_view.get_teammates(state.team_name, max_data_age=4)
    if len(team_members) is 0:
        return None
    return choice(team_members)
