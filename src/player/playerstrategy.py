from random import choice

import parsing
from constants import KICKABLE_MARGIN
from player import actions
from player.actions import Command
from player.player import PlayerState, DEFAULT_MODE, INTERCEPT_MODE, CHASE_MODE, POSSESSION_MODE
from player.world_objects import Coordinate, Ball
from utils import clamp, debug_msg


class Objective:
    def __init__(self, state: PlayerState, command_generator, completion_criteria, maximum_duration=1) -> None:
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

        deadline_reached = self.deadline <= state.now()
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
    def __init__(self, *args: [Objective]):
        self.objectives = []
        for o in args:
            self.objectives.append(o)
        self.completed_objectives = 0

    def should_recalculate(self, state: PlayerState):
        # Don't recalculate if there are any un-executed urgent commands
        if self.completed_objectives >= len(self.objectives):
            return True
        if self.completed_objectives == len(self.objectives) - 1:
            return self.objectives[self.completed_objectives].should_recalculate(state)
        return False

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


def _chase_objective(state):
    if state.is_near_ball() or not state.is_nearest_ball(1):
        state.mode = POSSESSION_MODE
        return determine_objective(state)
    return _rush_to_ball_objective(state)


def _pass_objective(state):
    pass_target = _choose_pass_target(state)
    if pass_target is not None:
        state.mode = DEFAULT_MODE
        return Objective(state, lambda: actions.pass_to_player(state, _choose_pass_target(state)), lambda: True, 1)

    # No suitable pass target
    return Objective(state, lambda: actions.look_for_pass_target(state), lambda: True, 1)


def _get_goalie_y_value(state):
    """
    Used for finding the wanted y value, that the goalie should take according to the ball position
    """
    goalie_coord: Coordinate = state.position.get_value()
    ball: Ball = state.world_view.ball.get_value()

    # If ball above goal
    if ball.coord.pos_y > 7.01:
        return 7.01
    elif -7.01 < ball.coord.pos_y and ball.coord.pos_y < 7.01:
        return ball.coord.pos_y
    else:
        return -7.01


def determine_objective_goalie(state: PlayerState):
    # if ball unknown
        # Locate
    if _ball_unknown(state):
        return Objective(state, lambda: actions.idle_orientation(state), lambda: True, 1)
    # Project ball 10 ticks
    # If ball intercepts goal line within 10 ticks, intercept ball
    if not _ball_unknown(state):
        ball: Ball = state.world_view.ball.get_value()
        if ball.will_hit_goal_within(10):
            # Try to perform an interception of the ball if possible
            intercept_point, ticks = state.ball_interception()
            if intercept_point is not None:
                if state.is_test_player():
                    state.mode = INTERCEPT_MODE
                return _intercept_objective(state)


    # Follow ball y value
    if state.position.is_value_known() and state.world_view.ball.is_value_known():
        goalie_coord: Coordinate = state.position.get_value()
        delta = 0.5
        optimal_y_value = _get_goalie_y_value(state)
        if abs(optimal_y_value - goalie_coord.pos_y) > delta:
            y_axis_adjustment = optimal_y_value - goalie_coord.pos_y
            return Objective(state, lambda: actions.positional_adjustment(state, Coordinate(0, y_axis_adjustment)), lambda: True, 1)
        else:
            return Objective(state, lambda: actions.idle_orientation(state), lambda: True, 1)

    # If near ball
        # Catch

    # If ball in hands, kick to player
        # Kick to player



def determine_objective(state: PlayerState):
    # Goalie
    if state.num == 1:
        return determine_objective_goalie(state)

    if state.is_test_player():
        debug_msg(str(state.now()) + " Mode : " + str(state.mode), "MODE")

    if state.mode is INTERCEPT_MODE:
        return _intercept_objective(state)

    if state.mode is CHASE_MODE:
        return _chase_objective(state)

    if state.mode is POSSESSION_MODE:
        return _pass_objective(state)

    last_see_update = state.action_history.last_see_update
    # Look for the ball when it's position is entirely unknown
    if _ball_unknown(state):
        return _locate_ball_objective(state)

    # If in possession of the ball
    if state.is_near_ball(KICKABLE_MARGIN):
        pass_target = _choose_pass_target(state)
        if pass_target is not None:
            return Objective(state, lambda: actions.pass_to_player(state, _choose_pass_target(state)), lambda: True, 1)

        # No suitable pass target
        return Objective(state, lambda: actions.look_for_pass_target(state), lambda: True, 1)

    # Try to perform an interception of the ball if possible
    intercept_point, ticks = state.ball_interception()
    if intercept_point is not None and state.world_view.ball.get_value().distance > 1.0:
        if state.is_test_player():
            debug_msg(str(state.now()) + " Intercepting!", "ACTIONS")
        state.mode = INTERCEPT_MODE
        debug_msg(str(state.now()) + "Player " + str(state.num) + " intercepting on " + str(intercept_point)
                                     + " at time " + str(state.now() + ticks), "INTERCEPTION")
        return _intercept_objective(state)

    # Retrieve the ball if you are one of the two closest players to the ball
    if state.is_nearest_ball(1):
        if state.is_test_player():
            debug_msg(str(state.now()) + " Rush to ball!", "ACTIONS")
        return _rush_to_ball_objective(state)

    # Finally, if ball is not heading directly towards player, reposition while looking at the ball
    if not state.ball_incoming():
        if state.is_test_player():
            debug_msg(str(state.now()) + " Position optimally!", "ACTIONS")
        return _position_optimally_objective(state)

    debug_msg(str(state.now()) + " Idle orientation!", "ACTIONS")
    return Objective(state, lambda: actions.idle_orientation(state), lambda: True, 1)


def _ball_unknown(state):
    seen_recently = state.world_view.ball.is_value_known(state.action_history.three_see_updates_ago)
    return state.is_ball_missing() or not seen_recently


def _locate_ball_objective(state: PlayerState):
    return Objective(state, lambda: actions.locate_ball(state),
                     lambda: state.world_view.ball.is_value_known(state.action_history.last_see_update), 1)


def _intercept_objective(state):
    ball: Ball = state.world_view.ball.get_value()
    dist = ball.distance

    if not ball.is_moving_closer():
        if dist < 15:
            state.mode = CHASE_MODE
            return determine_objective(state)

    intercept_point, tick = state.ball_interception()
    if intercept_point is not None and ball.distance > 1.0:
        return Objective(state, lambda: actions.intercept(state, intercept_point), lambda: state.is_near_ball())

    if state.ball_incoming():
        return Objective(state, lambda: actions.receive_ball(state), lambda: state.is_near_ball())
    else:
        state.mode = DEFAULT_MODE
        return determine_objective(state)


def _rush_to_ball_objective(state):
    return Objective(state, lambda: actions.rush_to_ball(state), lambda: state.is_near_ball(), 1)


def _position_optimally_objective(state: PlayerState):
    if state.player_type == "defender":
        optimal_position = _optimal_defender_pos(state)
    elif state.player_type == "midfield":
        optimal_position = _optimal_midfielder_pos(state)
    else:  # Striker
        optimal_position = _optimal_striker_pos(state) #_optimal_attacker_pos(state)

    current_position: Coordinate = state.position.get_value()
    dist = current_position.euclidean_distance_from(optimal_position)

    if dist > 6.0:  # todo: Should they sprint if dist > 10?
        target = optimal_position
        return Objective(state, lambda: actions.rush_to(state, target), lambda: True)
    if dist > 2.0:
        difference = optimal_position - current_position
        return Objective(state, lambda: actions.positional_adjustment(state, difference), lambda: True)
    else:
        return Objective(state, lambda: actions.idle_orientation(state), lambda: True)


def _optimal_striker_pos(state: PlayerState) -> Coordinate:
    side = 1 if state.world_view.side == 'l' else -1
    ball: Coordinate = state.world_view.ball.get_value().coord
    play_position = state.get_global_play_pos()
    ball_delta_y = ball.pos_y - play_position.pos_y

    if side * ball.pos_x > 0:
        # Attacking
        x_offset = ball.pos_x + side * 5
        optimal_x = clamp(play_position.pos_x + x_offset, -45, 45)

        # Used to make players position themselves closer to the goal on the y-axis when far up/down the field
        y_goal_factor = 0.982888 + 0.002871167 * abs(optimal_x) - 0.0000807057 * pow(optimal_x, 2)

        optimal_y = clamp(play_position.pos_y + ball.pos_y * 0.2 + ball_delta_y * 0.4, -30, 30) * y_goal_factor
        return Coordinate(optimal_x, optimal_y)
    else:
        # Defending
        optimal_x = -state.get_global_play_pos().pos_x + ball.pos_x * 0.4
        optimal_y = state.get_global_play_pos().pos_y + ball_delta_y * 0.2
        return Coordinate(optimal_x, optimal_y)


def _optimal_midfielder_pos(state) -> Coordinate:
    side = 1 if state.world_view.side == 'l' else -1
    ball: Coordinate = state.world_view.ball.get_value().coord
    play_position = state.get_global_play_pos()
    ball_delta_y = ball.pos_y - play_position.pos_y
    ball_delta_x = ball.pos_x - play_position.pos_x

    # Position player according to their starting position and the current ball position
    if side * ball.pos_x > 0:
        # Attacking
        optimal_x = clamp(play_position.pos_x + ball_delta_x * 0.4 + ball.pos_x * 0.6, -45, 45)
    else:
        # Defending
        optimal_x = clamp(play_position.pos_x + ball.pos_x * 0.4, -45, 45)


    # Used to make players position themselves closer to the goal on the y-axis when far up/down the field
    y_goal_factor = 1 - (abs(optimal_x) - 35) * 0.05 if abs(optimal_x) > 35 else 1.0
    optimal_y = clamp(play_position.pos_y + ball_delta_y * 0.2 + ball.pos_y * 0.2, -25, 25) * y_goal_factor

    return Coordinate(optimal_x, optimal_y)


def _optimal_defender_pos(state) -> Coordinate:
    side = 1 if state.world_view.side == 'l' else -1
    ball: Coordinate = state.world_view.ball.get_value().coord
    play_position = state.get_global_play_pos()
    ball_delta_y = ball.pos_y - play_position.pos_y
    ball_delta_x = ball.pos_x - play_position.pos_x

    # Position player according to their starting position and the current ball position
    optimal_x = play_position.pos_x + ball_delta_x * 0.4 + ball.pos_x * 0.4
    if side > 0:
        optimal_x = clamp(optimal_x, -45, -3)
    else:
        optimal_x = clamp(optimal_x, 3, 45)

    # Used to make players position themselves closer to the goal on the y-axis when far up/down the field
    y_goal_factor = 1 - (abs(optimal_x) - 35) * 0.05 if abs(optimal_x) > 35 else 1.0
    optimal_y = clamp(play_position.pos_y + ball.pos_y * 0.4 + ball_delta_y * 0.1, -25, 25) * y_goal_factor

    return Coordinate(optimal_x, optimal_y)


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