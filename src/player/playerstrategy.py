import math
from random import choice

from constants import KICKABLE_MARGIN, CATCHABLE_MARGIN, MINIMUM_TEAMMATES_FOR_PASS
from geometry import calculate_full_origin_angle_radians
from player import actions
from player.actions import Command, _calculate_relative_angle
from player.player import PlayerState, DEFAULT_MODE, INTERCEPT_MODE, CHASE_MODE, POSSESSION_MODE, CATCH_MODE, DRIBBLING_MODE
from player.world_objects import Coordinate, Ball
from utils import clamp, debug_msg


class Objective:
    def __init__(self, state: PlayerState, command_generator, completion_criteria=lambda: True, maximum_duration=1) -> None:
        self.command_generator = command_generator
        self.completion_criteria = completion_criteria
        self.deadline = state.now() + maximum_duration
        self.commands_executed = 0
        self.planned_commands: [Command] = []
        self.last_command_update_time = -1
        self.has_processed_see_update = False

    def should_recalculate(self, state: PlayerState):
        # Don't recalculate if there are any un-executed urgent commands
        if self.has_urgent_commands() or self.has_processed_see_update:
            return False

        deadline_reached = self.deadline <= state.now()
        return deadline_reached or self.completion_criteria()

    def get_next_commands(self, state: PlayerState):
        if (not self.has_urgent_commands()) and not self.has_processed_see_update:
            # Update planned commands after receiving a 'see' update
            self.planned_commands = self.command_generator()
            self.last_command_update_time = state.action_history.last_see_update
            self.commands_executed = 0
            self.has_processed_see_update = True

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


def _dribble_objective(state: PlayerState):
    side = 1 if state.world_view.side == "l" else -1
    if not state.is_nearest_ball(1):
        state.mode = DEFAULT_MODE
        return determine_objective(state)

    if not state.is_near_ball(KICKABLE_MARGIN):
        return _rush_to_ball_objective(state)

    pos: Coordinate = state.position.get_value()
    if pos.euclidean_distance_from(Coordinate(52.5 * side, 0)) < 24:
        return Objective(state, lambda: actions.shoot_to(state, Coordinate(55 * side, 0), 100), lambda: True, 1)

    if not state.action_history.has_looked_for_targets:
        debug_msg(str(state.now()) + "looking for pass targets", "DRIBBLE")
        state.action_history.has_looked_for_targets = True

        return Objective(state, lambda: actions.look_for_pass_target(state), lambda: len(state.world_view.get_teammates(state.team_name, max_data_age=3)) >= MINIMUM_TEAMMATES_FOR_PASS, 3)

    target = _choose_pass_target(state)
    if target is not None:
        return Objective(state, lambda: actions.pass_to_player(state, target), lambda: True, 1)

    if state.is_near_ball() and state.action_history.has_looked_for_targets:
        target_coord: Coordinate = Coordinate(52.5 * side, 0)
        opposing_goal_dir = math.degrees(calculate_full_origin_angle_radians(target_coord, state.position.get_value()))
        state.action_history.has_looked_for_targets = False
        return Objective(state, lambda: actions.dribble(state, int(opposing_goal_dir)), lambda: False, 1)
    return _rush_to_ball_objective(state)


def _pass_objective(state):
    if not state.is_near_ball():
        state.mode = DEFAULT_MODE
        return determine_objective(state)

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

    return clamp(ball.coord.pos_y * 0.8, -5, 5)


def _lost_orientation(state):
    return (not state.body_angle.is_value_known(state.action_history.last_see_update)) \
           or (not state.position.is_value_known(state.action_history.last_see_update))


def determine_objective_goalie(state: PlayerState):
    # Is grøntsag blind orient
    if _lost_orientation(state):
        return Objective(state, lambda: actions.blind_orient(state), lambda: True, 1)

    # Find ball
    if _ball_unknown(state):
        return Objective(state, lambda: actions.locate_ball(state), lambda: True, 1)

    # If catch ball successful or goal_kick, pass to teammate
    if state.world_view.game_state == "free_kick_{0}".format(state.world_view.side) or state.world_view.game_state == "goal_kick_{0}".format(state.world_view.side):
        if state.is_near_ball(KICKABLE_MARGIN):
            pass_target = _choose_pass_target(state)
            if pass_target is not None:
                return Objective(state, lambda: actions.pass_to_player(state, _choose_pass_target(state)), lambda: True, 1)
            # No suitable pass target
            return Objective(state, lambda: actions.look_for_pass_target(state), lambda: True, 1)
        else:
            return Objective(state, lambda: actions.jog_to(state, state.world_view.ball.get_value().coord), lambda: True, 1)

    ball: Ball = state.world_view.ball.get_value()

    # If in possession of the ball
    if state.is_near_ball(KICKABLE_MARGIN):
        return Objective(state, lambda: actions.shoot_to(state, Coordinate(0, 0), power=70), lambda: False, 50)

        pass_target = _choose_pass_target(state)
        if pass_target is not None:
            return Objective(state, lambda: actions.pass_to_player(state, _choose_pass_target(state)), lambda: True, 1)

        # No suitable pass target
        return Objective(state, lambda: actions.look_for_pass_target(state), lambda: True, 1)

    # Catch ball if close!
    positions = ball.project_ball_position(2, 0)
    position, direction, speed = ball.approximate_position_direction_speed(4)
    if positions is not None and speed > 0.2:
        ball_pos_1_tick: Coordinate = positions[0]
        # ball_pos_2_tick: Coordinate = positions[1]
        if ball_pos_1_tick.euclidean_distance_from(state.position.get_value()) < CATCHABLE_MARGIN:
            return Objective(state, lambda: actions.catch_ball(state, ball_pos_1_tick), lambda: True, 1)


    # Try to perform an interception of the ball if possible
    intercept_point, ticks = state.ball_interception()
    if intercept_point is not None and state.world_view.ball.get_value().distance > 0.5:
        return _intercept_objective_goalie(state)

    # If ball will hit goal soon, rush to position
    if ball.will_hit_goal_within(5):
        positions = ball.project_ball_position(2, 0)
        if positions is not None:
            return Objective(state, lambda: actions.rush_to(state, positions[1]), lambda: True, 1)

    # If ball within 2 meters, run to it
    if state.is_near_ball(7):
        return Objective(state, lambda: actions.rush_to(state, state.world_view.ball.get_value().coord), lambda: True, 1)

    # Stay close to y_pos of ball
    if state.position.is_value_known() and state.world_view.ball.is_value_known():
        goalie_coord: Coordinate = state.position.get_value()
        delta = 1.5
        optimal_y_value = _get_goalie_y_value(state)
        if abs(optimal_y_value - goalie_coord.pos_y) > delta or abs(goalie_coord.pos_x) - 50 > delta:
            if state.world_view.side == "l":
                return Objective(state, lambda: actions.jog_to(state, Coordinate(-50, optimal_y_value)), lambda: True, 1)
            else:
                return Objective(state, lambda: actions.jog_to(state, Coordinate(50, optimal_y_value)), lambda: True, 1)
        else:
            return Objective(state, lambda: actions.face_ball(state), lambda: True, 1)


def determine_objective(state: PlayerState):

    if state.world_view.game_state == 'before_kick_off':
        return Objective(state, lambda: actions.idle_orientation(state), lambda: True, 1)

    # Goalie
    if state.num == 1:
        return determine_objective_goalie(state)

    # Is grøntsag blind orient
    if _lost_orientation(state):
        return Objective(state, lambda: actions.blind_orient(state), lambda: True, 1)

    if state.is_test_player():
        debug_msg(str(state.now()) + " Mode : " + str(state.mode), "MODE")

    if state.mode is INTERCEPT_MODE:
        return _intercept_objective(state)

    if state.mode is DRIBBLING_MODE:
        return _dribble_objective(state)

    if state.mode is POSSESSION_MODE:
        return _pass_objective(state)

    last_see_update = state.action_history.last_see_update
    # Look for the ball when it's position is entirely unknown
    if _ball_unknown(state):
        return _locate_ball_objective(state)

    # If in possession of ball, dribble!
    if state.is_near_ball() and state.is_nearest_ball(1):
        state.mode = DRIBBLING_MODE
        return _dribble_objective(state)

    # Try to perform an interception of the ball if possible
    intercept_point, tick = state.ball_interception()
    if intercept_point is not None and state.world_view.ball.get_value().distance > 1.0:
        state.mode = INTERCEPT_MODE
        if intercept_point.euclidean_distance_from(state.position.get_value()) > KICKABLE_MARGIN:
            return Objective(state, lambda: actions.intercept(state, intercept_point), lambda: state.is_near_ball())
        else:
            return Objective(state, lambda: actions.receive_ball(state), lambda: state.is_near_ball())

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


def _intercept_objective_goalie(state):
    ball: Ball = state.world_view.ball.get_value()
    dist = ball.distance

    if not ball.is_moving_closer():
        if dist < 15:
            return _rush_to_ball_objective(state)

    intercept_point, tick = state.ball_interception()
    if intercept_point is not None and ball.distance > 0.5:
        if intercept_point.euclidean_distance_from(state.position.get_value()) > KICKABLE_MARGIN:
            return Objective(state, lambda: actions.intercept(state, intercept_point), lambda: state.is_near_ball())
        else:
            return Objective(state, lambda: actions.receive_ball(state), lambda: state.is_near_ball())

    else:
        return determine_objective_goalie(state)

def _intercept_objective(state):
    ball: Ball = state.world_view.ball.get_value()
    dist = ball.distance

    if not ball.is_moving_closer():
        if dist < 15:
            state.mode = DRIBBLING_MODE
            return determine_objective(state)

    intercept_point, tick = state.ball_interception()
    if intercept_point is not None and ball.distance > 1.0:
        if intercept_point.euclidean_distance_from(state.position.get_value()) > KICKABLE_MARGIN:
            return Objective(state, lambda: actions.intercept(state, intercept_point), lambda: state.is_near_ball())
        else:
            return Objective(state, lambda: actions.receive_ball(state), lambda: state.is_near_ball())

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
    side = 1 if state.world_view.side == "l" else -1
    team_members = state.world_view.get_teammates(state.team_name, max_data_age=5)
    if side == 1:
        good_targets = list(filter(lambda p: p.coord.pos_x * side > state.position.get_value().pos_x, team_members))
    else:
        good_targets = list(filter(lambda p: p.coord.pos_x * side < state.position.get_value().pos_x, team_members))
    if len(good_targets) < 1:
        # Todo filter out bad passes - Philip
        return None
    reverse = True if side == 1 else False
    good_target = list(sorted(good_targets, key=lambda p: p.coord.pos_x, reverse=reverse))[0]

    return good_target


def team_has_corner_kick(state):
    if state.world_view.side == "l":
        if state.world_view.game_state == "corner_kick_l":
            return True
    elif state.world_view.side == "r":
        if state.world_view.game_state == "corner_kick_r":
            return True

    return False