from random import choice

import parsing
from player import actions
from player.actions import Command
from player.player import PlayerState
from player.world_objects import Coordinate


class Objective:
    def __init__(self, state: PlayerState, command_generator, completion_criteria, maximum_duration=10) -> None:
        self.command_generator = command_generator
        self.completion_criteria = completion_criteria
        self.deadline = state.now() + maximum_duration
        self.commands_executed = 0
        self.planned_commands: [Command] = []
        self.last_command_update_time = -1

    def should_recalculate(self, state: PlayerState):
        # Don't recalculate if there are any un-executed urgent commands
        if self.has_urgent_commands() or self.last_command_update_time >= state.action_history.last_see_update:
            return False

        deadline_reached = self.deadline >= state.now()
        return deadline_reached or self.completion_criteria()

    def get_next_commands(self, state: PlayerState):
        if (not self.has_urgent_commands()) and self.last_command_update_time < state.action_history.last_see_update:
            # Update planned commands after receiving a 'see' update
            self.planned_commands = self.command_generator()
            self.last_command_update_time = state.action_history.last_see_update
            self.commands_executed = 0

        if self.commands_executed >= len(self.planned_commands):
            return []  # All planned commands have been executed, so don't do anything until next planning

        next_command = self.planned_commands[self.commands_executed]
        # Execute functions associated with command (such as projecting direction or position values)
        next_command.execute_attached_functions()
        self.commands_executed += 1
        return next_command.messages

    def has_urgent_commands(self):
        for command in self.planned_commands[self.commands_executed:]:
            if command.urgent:
                return True
        return False


def team_has_corner_kick(state):
    if state.world_view.side == "l":
        if state.world_view.game_state == "corner_kick_l":
            return True
    elif state.world_view.side == "r":
        if state.world_view.game_state == "corner_kick_r":
            return True

    return False


def determine_objective(state: PlayerState):
    last_see_update = state.action_history.last_see_update
    if state.is_ball_missing() or not state.world_view.ball.is_value_known(state.action_history.three_see_updates_ago):
        print(state.now(), " DETERMINE OBJECTIVE: LOCATE BALL. Last seen", state.world_view.ball.last_updated_time)
        return Objective(state, lambda: actions.locate_ball(state),
                         lambda: state.world_view.ball.is_value_known(last_see_update), 1)

    if state.is_nearest_ball(1):
        return Objective(state, lambda: actions.rush_to_ball(state), lambda: state.is_near_ball(), 5)

    return Objective(state, lambda: actions.idle_orientation(state), lambda: True, 1)
    return Objective(state, lambda: [], lambda: True, 1)

    target = state.get_global_play_pos()
    if state.num == 10:
        print(target)
    if not state.is_near(target, 0.5):
        return Objective(state, lambda: actions.go_to(state, state.get_global_play_pos()), lambda: True,
                         maximum_duration=10)

    return Objective(state, lambda: [], lambda: True, 1)

    if state.is_near(target, 0.5):
        return Objective(state, lambda: []
                         , lambda: False, maximum_duration=100)

    return Objective(state, lambda: actions.go_to(state, target)
                     , lambda: state.is_near(target, 0.5) and state.body_state.speed < 0.1, 100)

    if not state.world_view.ball.is_value_known(state.now() - 3):
        return Objective(lambda: actions.locate_ball(state))
    if state.is_near_ball():
        return Objective(lambda: actions.pass_ball_to_random(state))

    # Attempt interception if possible
    interception_position, interception_time = state.ball_interception()
    if interception_position is not None:
        print("Player " + str(state.num) + " intercepting at : " + str(interception_position) + " in " + str(
            interception_time))
        print(state.world_view.ball_speed())
        return Objective(lambda: actions.go_to(state, interception_position),
                         interception_time + 80)

    return Objective(lambda: actions.run_towards_ball(state))

    if current_objective is not None and not current_objective.should_recalculate() and not state.is_near_ball():
        return current_objective

    if team_has_corner_kick(state):
        # Left midfielder
        if state.num == 6:
            return Objective(lambda: actions.run_towards_ball(state), maximum_duration=5)

    if state.is_near_ball():
        if state.world_view.ball_speed() > 1.2:
            return Objective(lambda: actions.stop_ball(state))
        # If close to goal, dribble closer
        if state.is_approaching_goal():
            if state.world_view.side == "l":
                goal_pos = parsing._FLAG_COORDS.get("gr")
                return Objective(lambda: actions.dribble_towards(state, Coordinate(goal_pos[0], goal_pos[1])),
                                 maximum_duration=5)
            if state.world_view.side == "r":
                goal_pos = parsing._FLAG_COORDS.get("gl")
                return Objective(lambda: actions.dribble_towards(state, Coordinate(goal_pos[0], goal_pos[1])),
                                 maximum_duration=5)

        # otherwise find a pass target
        pass_target = _find_pass_target(state)
        if pass_target is None:
            if state.is_near_goal():
                return Objective(lambda: actions.kick_to_goal(state))
            return Objective(lambda: actions.look_for_pass_target(state))
        return Objective(lambda: actions.pass_ball_to(pass_target, state), maximum_duration=1)

    # Attempt interception if possible
    interception_position, interception_time = state.ball_interception()
    if interception_position is not None:
        print("Player " + str(state.num) + " intercepting at : " + str(interception_position))
        return Objective(lambda: actions.go_to(state, interception_position),
                         interception_time - 1)

    # If less than 15 meters from ball and one of two closest team players, then attempt to retrieve it
    if state.world_view.game_state == 'play_on' and state.world_view.ball.is_value_known(state.now() - 5):
        if state.is_nearest_ball(1):
            return Objective(lambda: actions.run_towards_ball(state), maximum_duration=1)

    target_position = state.get_global_play_pos()

    return Objective(lambda: actions.idle_orientation(state))
    if state.is_near(target_position):
        pass
    else:
        return Objective(lambda: actions.jog_towards(state, target_position))


def orient_objective(state: PlayerState):
    return Objective(lambda: actions.append_neck_orientation(state), maximum_duration=3)


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
