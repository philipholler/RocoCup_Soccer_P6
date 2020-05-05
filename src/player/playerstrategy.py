from random import choice

import parsing
from constants import KICKABLE_MARGIN
from player import actions
from player.actions import Command
from player.player import PlayerState
from player.world_objects import Coordinate, Ball
from utils import clamp


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


class CompositeObjective:

    def __init__(self, *args: [Objective]) -> None:
        self.objectives = []
        for o in args:
            self.objectives.append(o)
        self.completed_objectives = 0

    def should_recalculate(self, state: PlayerState):
        # Don't recalculate if there are any un-executed urgent commands
        if self.completed_objectives >= len(self.objectives):
            return True
        if self.completed_objectives == len(self.objectives) - 1:
            return self.objectives[len(self.objectives) - 1].should_recalculate(state)

    def get_next_commands(self, state: PlayerState):
        if self._current_objective().should_recalculate(state):
            self.completed_objectives += 1

        if self.completed_objectives >= len(self.objectives):
            return []

        return self._current_objective().get_next_commands(state)

    def has_urgent_commands(self):
        for objective in self.objectives:
            if objective.has_urgent_commands():
                return True
        return False

    def _current_objective(self) -> Objective:
        return self.objectives[self.completed_objectives]


def determine_objective(state: PlayerState):
    last_see_update = state.action_history.last_see_update
    if state.num != 1: # Every player except for goalie
        # Look for the ball when it's position is entirely unknown
        if _ball_unknown(state):
            return _locate_ball_objective(state)

        # If in possession of the ball
        if state.is_near_ball(KICKABLE_MARGIN):
            return Objective(state, lambda: actions.idle_orientation(state), lambda: True, 1)

        # Try to perform an interception of the ball if possible
        intercept_point, ticks = state.ball_interception()
        if intercept_point is not None:
            return _intercept_rush_to_objective(state, intercept_point)

        # Retrieve the ball if you are one of the two closest players to the ball
        if state.is_nearest_ball(2) and False: # TODO TEMPORARY FOR TESTING
            return _rush_to_ball_objective(state)

        # Finally, reposition while looking at the ball if no other
        # task needs to be performed right now
        return _position_optimally_objective(state)

    return Objective(state, lambda: actions.idle_orientation(state), lambda: True, 1)

    if state.is_near_ball():
        pass_target = _choose_pass_target(state)
        if pass_target is None:
            return Objective(state, lambda: actions.look_for_pass_target(state), lambda: True, 1)
        return Objective(state, lambda: actions.pass_to_player(state, pass_target), lambda: True, 1)

    if state.is_ball_missing() or not state.world_view.ball.is_value_known(state.action_history.three_see_updates_ago):
        # print(state.now(), " DETERMINE OBJECTIVE: LOCATE BALL. Last seen", state.world_view.ball.last_updated_time)
        return Objective(state, lambda: actions.locate_ball(state),
                         lambda: state.world_view.ball.is_value_known(last_see_update), 1)

    if state.is_nearest_ball(1):
        return Objective(state, lambda: actions.rush_to_ball(state), lambda: state.is_near_ball(), 5)

    return Objective(state, lambda: actions.idle_orientation(state), lambda: True, 1)


def _ball_unknown(state):
    seen_recently = state.world_view.ball.is_value_known(state.action_history.three_see_updates_ago)
    return state.is_ball_missing() or not seen_recently


def _locate_ball_objective(state: PlayerState):
    return Objective(state, lambda: actions.locate_ball(state),
                     lambda: state.world_view.ball.is_value_known(state.action_history.last_see_update), 1)


def _intercept_rush_to_objective(state, intercept_point):
    interception = Objective(state, lambda: actions.intercept(state, intercept_point), lambda: True, 15)
    follow_up = Objective(state, lambda: actions.rush_to_ball(state), lambda: state.is_near_ball(), 10)
    return CompositeObjective(interception, follow_up)


def _rush_to_ball_objective(state):
    return Objective(state, lambda: actions.rush_to_ball(state), lambda: state.is_near_ball(), 10)


def _position_optimally_objective(state: PlayerState):
    ball_position: Coordinate = state.world_view.ball.get_value().coord
    positional_offset: Coordinate = ball_position
    play_position = state.get_global_play_pos()

    # Position player according to their starting position and the current ball position
    optimal_x = clamp(play_position.pos_x + positional_offset.pos_x * 0.5, -45, 45)

    # Used to make players position themselves closer to the goal on the y-axis when far up/down the field
    y_goal_factor = 1 - (abs(optimal_x) - 35) * 0.05 if abs(optimal_x) > 35 else 1
    optimal_y = clamp(play_position.pos_y + positional_offset.pos_y * 0.2, -25, 25) * y_goal_factor
    optimal_position = Coordinate(optimal_x, optimal_y)

    current_position: Coordinate = state.position.get_value()
    dist = current_position.euclidean_distance_from(optimal_position)

    if dist > 6.0:
        target = optimal_position
        return Objective(state, lambda: actions.jog_to(state, target), lambda: True)
    if dist > 2.0:  # todo: if dist > 6 jog towards?
        difference = optimal_position - current_position
        return Objective(state, lambda: actions.positional_adjustment(state, difference), lambda: True)
    else:
        return Objective(state, lambda: actions.idle_orientation(state), lambda: True)


def _find_player(state, player_num):
    team_players = state.world_view.get_teammates(state.team_name, max_data_age=4)
    for p in team_players:
        if p.num is not None and int(p.num) == int(player_num):
            return p
    return None


def _choose_pass_target(state: PlayerState):
    """if state.coach_command.is_value_known(state.now() - 7 * 10):
        coach_command = state.coach_command.get_value()
        if "pass" in coach_command:
            pass_pairs = parsing.parse_pass_command(coach_command)

            for from_player, to_player in pass_pairs:
                if state.num == from_player:
                    return find_player(state, to_player)"""

    team_members = state.world_view.get_teammates(state.team_name, max_data_age=5)
    if len(team_members) is 0:
        return None
    return sorted(team_members, key=lambda p: p.coord.pos_x)[0]


def team_has_corner_kick(state):
    if state.world_view.side == "l":
        if state.world_view.game_state == "corner_kick_l":
            return True
    elif state.world_view.side == "r":
        if state.world_view.game_state == "corner_kick_r":
            return True

    return False