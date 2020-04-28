from random import choice

import parsing
from player import actions
from player.player import PlayerState
from player.world_objects import Coordinate


class Objective:
    def __init__(self, action_planner, time_out=0) -> None:
        self.time_out = time_out
        self.action_planner = action_planner

    def should_recalculate(self):
        self.time_out -= 1
        return self.time_out <= 0

    def plan_actions(self):
        return self.action_planner()


def team_has_corner_kick(state):
    if state.world_view.side == "l":
        if state.world_view.game_state == "corner_kick_l":
            return True
    elif state.world_view.side == "r":
        if state.world_view.game_state == "corner_kick_r":
            return True

    return False


def determine_objective(state: PlayerState, current_objective: Objective):
    if not state.world_view.ball.is_value_known(state.now() - 3):
        return Objective(lambda: actions.locate_ball(state))

    if current_objective is not None and not current_objective.should_recalculate() and not state.is_near_ball():
        return current_objective

    if team_has_corner_kick(state):
        # Left midfielder
        if state.num == 6:
            return Objective(lambda: actions.run_towards_ball(state), time_out=5)

    if state.is_near_ball():
        # If close to goal, dribble closer
        if state.is_approaching_goal():
            if state.world_view.side == "l":
                goal_pos = parsing._FLAG_COORDS.get("gr")
                return Objective(lambda: actions.dribble_towards(state, Coordinate(goal_pos[0], goal_pos[1])), time_out=5)
            if state.world_view.side == "r":
                goal_pos = parsing._FLAG_COORDS.get("gl")
                return Objective(lambda: actions.dribble_towards(state, Coordinate(goal_pos[0], goal_pos[1])), time_out=5)

        # otherwise find a pass target
        pass_target = _find_pass_target(state)
        if pass_target is None:
            if state.is_near_goal():
                return Objective(lambda: actions.kick_to_goal(state))
            print("no one to kick to")
            return Objective(lambda: actions.look_for_pass_target(state))
        print("kick!")
        return Objective(lambda: actions.pass_ball_to(pass_target, state), time_out=1)

    # Attempt interception if possible
    interception_position, interception_time = state.ball_interception()
    if interception_position is not None:
        print("Player " + str(state.num) + " intercepting at : " + str(interception_position))
        return Objective(lambda: actions.run_towards(state, interception_position),
                         interception_time - 1)

    # If less than 15 meters from ball and one of two closest team players, then attempt to retrieve it
    if state.world_view.game_state == 'play_on' and state.world_view.ball.is_value_known(state.now() - 5):
        if state.is_nearest_ball(1):
            return Objective(lambda: actions.run_towards_ball(state), time_out=1)

    target_position = state.get_global_play_pos()

    if state.is_near(target_position):
        return Objective(lambda: actions.idle_orientation(state))
    else:
        return Objective(lambda: actions.jog_towards(state, target_position))


def orient_objective(state: PlayerState):
    return Objective(lambda: actions.idle_neck_orientation(state), time_out=3)


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
