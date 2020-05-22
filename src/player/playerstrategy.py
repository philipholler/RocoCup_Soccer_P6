import math
import random
import re
from random import choice

import constants

import constants
from constants import KICKABLE_MARGIN, CATCHABLE_MARGIN, MINIMUM_TEAMMATES_FOR_PASS
from constants import KICKABLE_MARGIN, CATCHABLE_MARGIN, MINIMUM_TEAMMATES_FOR_PASS, DRIBBLE_INDICATOR, PASS_INDICATOR
from geometry import calculate_full_origin_angle_radians
from player import actions
from player.actions import Command, _calculate_relative_angle
from player.player import PlayerState, DEFAULT_MODE, INTERCEPT_MODE, CHASE_MODE, POSSESSION_MODE, CATCH_MODE, \
    DRIBBLING_MODE
from player.world_objects import Coordinate, Ball, ObservedPlayer, PrecariousData
from utils import clamp, debug_msg


class Objective:
    def __init__(self, state: PlayerState, command_generator, completion_criteria=lambda: True,
                 maximum_duration=1) -> None:
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

    should_dribble = state.received_dribble_instruction.get_value() \
                     and state.received_dribble_instruction.last_updated_time >= state.now() - 100

    if not should_dribble:
        target = _choose_pass_target(state)
        if target is not None:
            return Objective(state, lambda: actions.pass_to_player(state, target), lambda: True, 1)
    else:
        state.received_dribble_instruction.set_value(False, state.now())

    if state.is_near_ball():  # todo temp: and state.action_history.has_looked_for_targets:
        target_coord: Coordinate = Coordinate(52.5 * side, 0)
        opposing_goal_dir = math.degrees(calculate_full_origin_angle_radians(target_coord, state.position.get_value()))
        state.action_history.has_looked_for_targets = False
        return Objective(state, lambda: actions.dribble(state, int(opposing_goal_dir)), lambda: False, 1)
    return _rush_to_ball_objective(state)


def _pass_objective(state, must_pass: bool = False):
    if not state.is_near_ball():
        state.mode = DEFAULT_MODE
        return determine_objective(state)

    pass_target = _choose_pass_target(state, must_pass)
    if pass_target is not None:
        state.mode = DEFAULT_MODE
        return Objective(state, lambda: actions.pass_to_player(state, pass_target), lambda: True, 1)

    # No suitable pass target
    return Objective(state, lambda: actions.look_for_pass_target(state), lambda: True, 1)


def _get_goalie_y_value(state):
    """
    Used for finding the wanted y value, that the goalie should take according to the ball position
    """
    ball: Ball = state.world_view.ball.get_value()

    return clamp(ball.coord.pos_y * 0.8, -5, 5)


def _lost_orientation(state):
    return (not state.body_angle.is_value_known(state.action_history.two_see_updates_ago)) \
           or (not state.position.is_value_known(state.action_history.two_see_updates_ago))


def determine_objective_goalie_default(state: PlayerState):
    opponent_side = "r" if state.world_view.side == "l" else "l"
    # If goalie and goal_kick -> Go to ball and pass
    if state.world_view.game_state == "goal_kick_{0}".format(state.world_view.side) and state.num == 1:
        debug_msg(str(state.now()) + " | goal kick -> got to ball and pass", "GOALIE")
        if state.is_near_ball(KICKABLE_MARGIN):
            return _pass_objective(state, must_pass=True)
        else:
            return _jog_to_ball_objective(state)

    # If game not started or other team starting -> Idle orientation
    if state.world_view.game_state == 'before_kick_off' or state.world_view.game_state == "kick_off_{0}".format(
            opponent_side) or ("goal_r" == state.world_view.game_state or "goal_l" == state.world_view.game_state):
        debug_msg(str(state.now()) + " | If game not started or other team starting -> Idle orientation", "GOALIE")
        return Objective(state, lambda: actions.idle_orientation(state), lambda: True, 1)

    # If lost_orientation -> blind orient
    if _lost_orientation(state):
        debug_msg(str(state.now()) + " | lost orientation -> blind orient", "GOALIE")
        return Objective(state, lambda: actions.blind_orient(state), lambda: True, 1)

    # If ball unknown -> locate ball
    if _ball_unknown(state):
        debug_msg(str(state.now()) + " | ball unknown -> locate ball", "GOALIE")
        return Objective(state, lambda: actions.locate_ball(state), lambda: True, 1)

    # If some fault has been made by our team -> Position optimally
    if "fault_{0}".format(state.world_view.side) in state.world_view.game_state:
        debug_msg(str(state.now()) + " | Team made fault -> position optimally", "GOALIE")
        return _position_optimally_objective_goalie(state)

    # If we have a free kick, corner_kick, kick_in, kick_off or goal_kick
    # If closest -> Go to ball and pass, else position optimally
    if state.world_view.game_state == "free_kick_{0}".format(state.world_view.side) \
            or state.world_view.game_state == "corner_kick_{0}".format(state.world_view.side) \
            or state.world_view.game_state == "kick_in_{0}".format(state.world_view.side) \
            or state.world_view.game_state == "goal_kick_{0}".format(state.world_view.side) \
            or state.world_view.game_state == "offside_{0}".format(opponent_side):
        debug_msg(str(
            state.now()) + " | free_kick, corner_kick, kick_in, kick_off, goal_kick, offside -> go to ball or position optimally",
                  "GOALIE")
        if _ball_unknown(state):
            return _locate_ball_objective(state)
        if state.is_near_ball(KICKABLE_MARGIN):
            if state.world_view.sim_time - state.action_history.last_look_for_pass_targets > 2:
                return Objective(state, lambda: actions.look_for_pass_target(state), lambda: True, 2)
            if _choose_pass_target(state, must_pass=True) is not None:
                return Objective(state,
                                 lambda: actions.pass_to_player(state, _choose_pass_target(state, must_pass=True)),
                                 lambda: True, 1)
            else:
                return Objective(state, lambda: actions.look_for_pass_target(state), lambda: True, 2)
        elif state.is_nearest_ball(1):
            return _jog_to_ball_objective(state)
        else:
            return _position_optimally_objective_goalie(state)

    ball: Ball = state.world_view.ball.get_value()

    # If in possession of the ball -> Pass to team mate
    if state.is_near_ball(KICKABLE_MARGIN):
        pass_target = _choose_pass_target(state)
        if pass_target is not None:
            debug_msg(str(state.now()) + " | in possession, pass target found -> pass to teammate", "GOALIE")
            return Objective(state, lambda: actions.pass_to_player(state, _choose_pass_target(state)), lambda: True, 1)
        # No suitable pass target
        debug_msg(str(state.now()) + " | in possession, pass target not found -> look for pass target", "GOALIE")
        return Objective(state, lambda: actions.look_for_pass_target(state), lambda: True, 1)

    # If ball coming to goalie inside box -> Catch ball
    positions = ball.project_ball_position(2, 0)
    if positions is not None and state.is_inside_own_box():
        debug_msg(str(state.now()) + " | Ball incoming inside box -> Catch ball", "GOALIE")
        ball_pos_1_tick: Coordinate = positions[0]
        if ball_pos_1_tick.euclidean_distance_from(state.position.get_value()) < CATCHABLE_MARGIN:
            return Objective(state, lambda: actions.catch_ball(state, ball_pos_1_tick), lambda: True, 1)

    # If ball coming towards us or ball will hit goal soon -> Intercept
    if (ball.will_hit_goal_within(ticks=5) or (state.is_nearest_ball(1) and state.is_ball_inside_own_box())):
        debug_msg(str(state.now()) + " | ball coming towards us or ball will hit goal soon -> run to ball and catch!",
                  "GOALIE")
        intercept_actions = actions.intercept_2(state, "catch")
        if intercept_actions is not None:
            return Objective(state, lambda: intercept_actions)
        else:
            return _rush_to_ball_objective(state)

    # If position not alligned with ball y-position -> Adjust y-position
    if state.position.is_value_known() and state.world_view.ball.is_value_known() and not constants.USING_PASS_CHAIN_STRAT:
        debug_msg(str(state.now()) + " | Position not optimal -> adjust position", "GOALIE")
        return _position_optimally_objective_goalie(state)

    # If nothing to do -> Face ball
    debug_msg(str(state.now()) + " | Nothing to do -> Face ball", "GOALIE")
    return Objective(state, lambda: actions.face_ball(state), lambda: True, 1)


def calculate_required_degree(state):
    if (state.world_view.side == 'l' and state.world_view.ball.get_value().coord.pos_x < -15) \
            or (state.world_view.side == 'r' and state.world_view.ball.get_value().coord.pos_x > 15):
        for op in state.world_view.get_opponents(state.team_name, 10):
            op: ObservedPlayer
            if op.coord.euclidean_distance_from(state.world_view.ball.get_value().coord) < 4:
                return 2

    return 1


def determine_objective_field_default(state: PlayerState):
    state.intercepting = False
    # If lost orientation -> blind orient
    if _lost_orientation(state):
        return Objective(state, lambda: actions.blind_orient(state), lambda: True, 1)

    opponent_side = "r" if state.world_view.side == "l" else "l"
    # If game not started or other team starting -> Idle orientation
    if state.world_view.game_state == 'before_kick_off' or state.world_view.game_state == "kick_off_{0}".format(
            opponent_side) or "goal" in state.world_view.game_state:
        return Objective(state, lambda: actions.idle_orientation(state), lambda: True, 1)

    # If some fault has been made by our team -> position optimally
    if "fault_{0}".format(state.world_view.side) in state.world_view.game_state:
        return _position_optimally_objective(state)

    # If we have a free kick, corner_kick, kick_in or kick_off
    #   If closest -> Go to ball and pass, else position optimally
    if state.world_view.game_state == "free_kick_{0}".format(state.world_view.side) \
            or state.world_view.game_state == "corner_kick_{0}".format(state.world_view.side) \
            or state.world_view.game_state == "kick_in_{0}".format(state.world_view.side) \
            or state.world_view.game_state == "kick_off_{0}".format(state.world_view.side) \
            or state.world_view.game_state == "offside_{0}".format(opponent_side):
        if _ball_unknown(state):
            return _locate_ball_objective(state)
        if state.is_near_ball(KICKABLE_MARGIN):
            if state.world_view.sim_time - state.action_history.last_look_for_pass_targets > 2:
                return Objective(state, lambda: actions.look_for_pass_target(state), lambda: True, 2)
            if _choose_pass_target(state, must_pass=True) is not None:
                return Objective(state,
                                 lambda: actions.pass_to_player(state, _choose_pass_target(state, must_pass=True)),
                                 lambda: True, 1)
            else:
                return Objective(state, lambda: actions.look_for_pass_target(state), lambda: True, 2)
        elif state.is_nearest_ball(1):
            return _jog_to_ball_objective(state)
        else:
            return _position_optimally_objective(state)

    # If in dribbling mode -> Dribble
    if state.mode is DRIBBLING_MODE:
        return _dribble_objective(state)

    # If in possession mode -> Pass
    if state.mode is POSSESSION_MODE:
        return _pass_objective(state)

    # If position known, but ball not -> Locate ball
    if _ball_unknown(state):
        return _locate_ball_objective(state)

    # If in possession of ball -> dribble!
    if state.is_near_ball() and state.is_nearest_ball(1):
        state.mode = DRIBBLING_MODE
        return _dribble_objective(state)

    required_degree = calculate_required_degree(state)
    if state.is_nearest_ball(required_degree):
        intercept_actions = actions.intercept_2(state)
        state.intercepting = True
        if intercept_actions is not None:
            return Objective(state, lambda: intercept_actions)
        else:
            return _rush_to_ball_objective(state)

    # If ball not incoming -> Position optimally while looking at ball
    if not state.ball_incoming() and not constants.USING_PASS_CHAIN_STRAT:
        if state.is_test_player():
            debug_msg(str(state.now()) + " Position optimally!", "ACTIONS")
        return _position_optimally_objective(state)

    if state.is_test_player():
        debug_msg(str(state.now()) + " Idle orientation!", "ACTIONS")

    return Objective(state, lambda: actions.idle_orientation(state), lambda: True, 1)


def determine_objective_position_only(state: PlayerState):
    # If lost orientation -> blind orient
    if _lost_orientation(state):
        return Objective(state, lambda: actions.blind_orient(state), lambda: True, 1)

    # If ball unknown -> locate ball
    if _ball_unknown(state):
        return Objective(state, lambda: actions.locate_ball(state), lambda: True, 1)

    if state.player_type == "goalie":
        return _position_optimally_objective_goalie(state)
    return _position_optimally_objective(state)


def determine_objective_biptest(state: PlayerState):
    # If lost orientation -> blind orient
    if _lost_orientation(state):
        return Objective(state, lambda: actions.blind_orient(state), lambda: True, 1)

    # If ball unknown -> locate ball
    if _ball_unknown(state):
        return Objective(state, lambda: actions.locate_ball(state), lambda: True, 1)

    if state.position.is_value_known():
        side: int = 1 if state.world_view.side == "l" else -1
        lower_goal: Coordinate = Coordinate(-25 * side, -33)
        upper_goal: Coordinate = Coordinate(-25 * side, 33)
        if not state.is_near(upper_goal, 2):
            debug_msg("Going to left goal", "BIPTEST")
            return Objective(state, lambda: actions.rush_to(state, upper_goal), lambda: state.is_near(upper_goal, 0.5),
                             1000)
        else:
            debug_msg("Going to right goal", "BIPTEST")
            return Objective(state, lambda: actions.rush_to(state, lower_goal), lambda: state.is_near(lower_goal, 0.5),
                             1000)


def determine_objective_goalie_positioning_striker(state: PlayerState):
    # If lost orientation -> blind orient
    if _lost_orientation(state):
        return Objective(state, lambda: actions.blind_orient(state), lambda: True, 1)

    # If ball unknown -> locate ball
    if _ball_unknown(state):
        return Objective(state, lambda: actions.locate_ball(state), lambda: True, 1)

    side = 1 if state.world_view.side == "l" else -1
    if state.world_view.sim_time > 75 and len(state.coach_commands) > 0:
        # First check for dribble, and dribble if needed
        dribble_in_commands: bool = False
        for command in state.coach_commands:
            cmd = command.get_value()
            if "dribble" in cmd and not state.goalie_position_strat_have_dribbled:
                dribble_in_commands = True
                dribble_dir = int(str(cmd).replace("(dribble ", "")[:-1])
                state.goalie_position_strat_have_dribbled = True
                return Objective(state, lambda: actions.dribble(state, int(dribble_dir), dribble_kick_power=20),
                                 lambda: True, 1)

        # If already dribble or should not dribble
        if not dribble_in_commands or state.goalie_position_strat_have_dribbled:
            if not state.is_near_ball():
                return _rush_to_ball_objective(state)

            if state.world_view.sim_time > 75:
                for command in state.coach_commands:
                    cmd = command.get_value()
                    if "striker_target_y" in cmd:
                        target_y_value = int(cmd[cmd.index(" ") + 1:-1])

                return Objective(state, lambda: actions.shoot_to(state, Coordinate(55 * side, target_y_value), 75),
                                 lambda: True, 1)

    return Objective(state, lambda: [], lambda: True, 1)


def determine_objective(state: PlayerState):
    if state.objective_behaviour == "field":
        return determine_objective_field_default(state)
    if state.objective_behaviour == "goalie_positioning_striker":
        return determine_objective_goalie_positioning_striker(state)
    if state.objective_behaviour == "position_optimally":
        return determine_objective_position_only(state)
    if state.objective_behaviour == "biptest":
        return determine_objective_biptest(state)
    if state.objective_behaviour == "default":
        if state.player_type == "goalie":
            return determine_objective_goalie_default(state)
        else:
            return determine_objective_field_default(state)
    elif state.objective_behaviour == "idle_orientation":
        return Objective(state, lambda: actions.idle_orientation(state), lambda: True, 1)
    elif state.objective_behaviour == "idle":
        return Objective(state, lambda: [], lambda: True, 1)
    else:
        raise Exception("Unknown objective behaviour pattern: " + state.objective_behaviour)


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
        return determine_objective(state)


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


def _jog_to_ball_objective(state):
    return Objective(state, lambda: actions.jog_to_ball(state), lambda: state.is_near_ball(), 1)


def _optimal_goalie_pos(state: PlayerState):
    if state.team_name in constants.GOALIE_MODEL_TEAMS:
        if state.goalie_position_strategy is not None:
            optimal_coord = Coordinate(state.goalie_position_strategy.pos_x, state.goalie_position_strategy.pos_y)
            state.goalie_position_strategy = None
            return optimal_coord
        else:
            ball: Ball = state.world_view.ball.get_value()

            y_value = clamp(ball.coord.pos_y * 0.8, -5, 5)

            return Coordinate(state.get_global_start_pos().pos_x, y_value)
    else:
        ball: Ball = state.world_view.ball.get_value()

        y_value = clamp(ball.coord.pos_y * 0.8, -5, 5)

        return Coordinate(state.get_global_start_pos().pos_x, y_value)


def _position_optimally_objective_goalie(state: PlayerState):
    if "kick_off" in state.world_view.game_state:
        # If already close to starting position, do idle orientation
        if state.position.get_value().euclidean_distance_from(state.get_global_start_pos()) < 2:
            return Objective(state, lambda: actions.idle_orientation(state), lambda: True)
        return Objective(state, lambda: actions.jog_to(state, state.get_global_start_pos()), lambda: True)

    optimal_position = _optimal_goalie_pos(state)

    current_position: Coordinate = state.position.get_value()
    dist = current_position.euclidean_distance_from(optimal_position)

    if dist > 6.0:
        target = optimal_position
        return Objective(state, lambda: actions.rush_to(state, target), lambda: True)
    if dist > 0.6:
        difference = optimal_position - current_position
        return Objective(state, lambda: actions.positional_adjustment(state, difference), lambda: True)
    else:
        return Objective(state, lambda: actions.idle_orientation(state), lambda: True)


def _position_optimally_objective(state: PlayerState):
    if "kick_off" in state.world_view.game_state:
        # If already close to starting position, do idle orientation
        if state.position.get_value().euclidean_distance_from(state.get_global_start_pos()) < 2:
            return Objective(state, lambda: actions.idle_orientation(state), lambda: True)
        return Objective(state, lambda: actions.jog_to(state, state.get_global_start_pos()), lambda: True)

    if state.player_type == "defender":
        optimal_position = _optimal_defender_pos(state)
    elif state.player_type == "midfield":
        optimal_position = _optimal_midfielder_pos(state)
    elif state.player_type == "goalie":
        optimal_position = _optimal_goalie_pos(state)
    else:  # Striker
        optimal_position = _optimal_striker_pos(state)  # _optimal_attacker_pos(state)

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
    if not state.world_view.ball.is_value_known():
        return state.get_global_play_pos()
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

        if state.world_view.team_has_ball(state.team_name, max_data_age=4):
            opt_coord = Coordinate(optimal_x + (10 * side), optimal_y)
            free_pos = state.get_closest_free_position(opt_coord)
            if state.is_test_player():
                debug_msg("Free position:{0}".format(free_pos), "FREE_POSITION")
            return opt_coord if free_pos is None else free_pos

        return Coordinate(optimal_x, optimal_y)
    else:
        # Defending
        optimal_x = -state.get_global_play_pos().pos_x + ball.pos_x * 0.4
        optimal_y = state.get_global_play_pos().pos_y + ball_delta_y * 0.2

        if state.world_view.team_has_ball(state.team_name, max_data_age=4):
            opt_coord = Coordinate(optimal_x + (10 * side), optimal_y)
            free_pos = state.get_closest_free_position(opt_coord)
            if state.is_test_player():
                debug_msg("Free position:{0}".format(free_pos), "FREE_POSITION")
            return opt_coord if free_pos is None else free_pos

        return Coordinate(optimal_x, optimal_y)


def _optimal_midfielder_pos(state) -> Coordinate:
    side = 1 if state.world_view.side == 'l' else -1
    if not state.world_view.ball.is_value_known():
        return state.get_global_play_pos()
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

    if state.world_view.team_has_ball(state.team_name, max_data_age=4):
        opt_coord = Coordinate(optimal_x + (10 * side), optimal_y)
        free_pos = state.get_closest_free_position(opt_coord)
        if state.is_test_player():
            debug_msg("Free position:{0}".format(free_pos), "FREE_POSITION")
        return opt_coord if free_pos is None else free_pos

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

    if state.world_view.team_has_ball(state.team_name, max_data_age=4):
        return Coordinate(optimal_x + (10 * side), optimal_y)

    return Coordinate(optimal_x, optimal_y)


def _find_player(state, player_num):
    team_players = state.world_view.get_player_observations(state.team_name, max_data_age=4)
    for p in team_players:
        if p.num is not None and int(p.num) == int(player_num):
            return p
    return None


def is_offside(state: PlayerState, target):
    if state.world_view.side is 'l':
        if target.coord.pos_x < 10:
            return False
    else:
        if target.coord.pos_x > -10:
            return False

    opponents = state.world_view.get_opponents(state.team_name, 10)

    for o in opponents:
        if state.world_view.side is 'l' and o.coord.pos_x > target.coord.pos_x:
            return False
        if state.world_view.side is 'r' and o.coord.pos_x < target.coord.pos_x:
            return False

    return True


def _choose_pass_target(state: PlayerState, must_pass: bool = False):
    print("choose pass target")
    """
    If uppaal has been generated recently -> Follow strat if applicable
    If free targets forward -> Pass forward
    If no free targets forward, but i am not marked -> dribble forward
    If no free targets forward, but free targets behind, and i am marked -> Pass back
    If no free targets and i am marked -> Try to dribble anyway
    :return: Parse target or None, if dribble
    """

    # For pass chain model, if an existing target is seen by player, pass ball
    if len(state.passchain_targets) > 0:
        print("passchain longer than 0")
        for target in state.passchain_targets:
            target: PrecariousData
            if target.last_updated_time > state.now() - 40:
                print("if target update time is later than 40 seconds ago")
                target = state.find_teammate_closest_to(target.get_value(), max_distance_delta=8.0)
                if target is not None:
                    print("TORGET ACQUIRED : ", target)
                    return target

    debug_msg(str(state.now()) + "Choosing pass target", "DRIBBLE_PASS_MODEL")
    # Act according to Possession model
    if state.dribble_or_pass_strat.is_value_known():
        if state.dribble_or_pass_strat.is_value_known(state.now() - 8):
            debug_msg("Following uppaal DribbleOrPass strategy :" + str(state.dribble_or_pass_strat.get_value())
                      , "DRIBBLE_PASS_MODEL")
            strat = state.dribble_or_pass_strat.get_value()
            state.dribble_or_pass_strat = PrecariousData.unknown()
            if DRIBBLE_INDICATOR in strat:
                if not must_pass:
                    state.statistics.use_possession_strategy()
                    debug_msg(str(state.now()) + " Dribble!", "DRIBBLE_PASS_MODEL")
                    return None

            else:
                match = re.match(r'.*\(([^,]*), ([^)]*)\)', strat)
                x = float(match.group(1))
                y = float(match.group(2))
                target = state.find_teammate_closest_to(Coordinate(x, y), max_distance_delta=3.0)
                if target is not None:
                    debug_msg(str(state.now()) + " DRIBBLE_PASS_MODEL : Playing to :" + str(Coordinate(x, y)),
                              "DRIBBLE_PASS_MODEL")

                    # If target is outside the no no square then return target
                    i = -1 if state.world_view.side == "l" else 1
                    is_too_far_back = True if (state.world_view.side == "l" and target.coord.pos_x < -36) \
                                              or (state.world_view.side == "r" and target.coord.pos_x > 36) else False

                    if (not is_too_far_back) and (not is_offside(state, target)) and (target.coord.pos_y > -20 or target.coord.pos_y > 20):
                        state.statistics.use_possession_strategy()
                        return target
                else:
                    debug_msg(str(state.now()) + "No teammate matched :" + str(
                        Coordinate(x, y)) + " Visible: " + str(state.world_view.get_teammates(state.team_name, 10))
                              , "DRIBBLE_PASS_MODEL")

        # Discard strategy
        state.statistics.discard_possession_strategy()
        state.dribble_or_pass_strat = PrecariousData.unknown()

    side = state.world_view.side

    """ # TODO : TESTING ONLY ----------------------------------------------------------
    teammates = state.world_view.get_teammates(state.team_name, 2)
    if len(teammates) is not 0:
        return choice(teammates)
    # todo -------------------------------------------------------------------------- """

    am_i_marked = state.world_view.is_marked(team=state.team_name, max_data_age=4, min_distance=4)

    # If free targets forward -> Pass forward
    forward_team_mates = state.world_view.get_non_offside_forward_team_mates(state.team_name, side,
                                                                             state.position.get_value(), max_data_age=4,
                                                                             min_distance_free=2, min_dist_from_me=2)



    if len(forward_team_mates) > 0:
        # If free team mates sort by closest to opposing teams goal
        opposing_team_goal: Coordinate = Coordinate(52.5, 0) if side == "l" else Coordinate(-52.5, 0)
        debug_msg("forward_team_mates: " + str(forward_team_mates), "PASS_TARGET")
        good_target = list(sorted(forward_team_mates, key=lambda p: p.coord.euclidean_distance_from(opposing_team_goal),
                                  reverse=False))[0]
        return good_target

    # If no free targets forward, but i am not marked -> dribble forward
    if len(forward_team_mates) < 1 and not am_i_marked:
        debug_msg("No free targets forward -> Dribble!", "PASS_TARGET")
        if must_pass:
            tms = state.world_view.get_teammates(state.team_name, 5)
            if len(tms) > 0:
                return random.choice(tms)
        return None

    # If no free targets forward, but free targets behind, and i am marked -> Pass back
    behind_team_mates = state.world_view.get_free_behind_team_mates(state.team_name, side, state.position.get_value(),
                                                                    max_data_age=3, min_distance_free=3,
                                                                    min_dist_from_me=3)
    if len(behind_team_mates) > 0:
        # Get the player furthest forward and free
        opposing_team_goal: Coordinate = Coordinate(52.5, 0) if side == "l" else Coordinate(-52.5, 0)
        debug_msg("Behind_team_mates: " + str(behind_team_mates), "PASS_TARGET")
        good_target = list(sorted(behind_team_mates, key=lambda p: p.coord.euclidean_distance_from(opposing_team_goal),
                                  reverse=False))[0]
        return good_target

    # If no free targets and i am marked -> Try to dribble anyway
    debug_msg("No free targets forward and i am marked -> Dribble anyway!", "PASS_TARGET")
    if must_pass:
        tms = state.world_view.get_player_observations(state.team_name, 3)
        if len(tms) > 0:
            return random.choice(tms)
    return None


def team_has_corner_kick(state):
    if state.world_view.side == "l":
        if state.world_view.game_state == "corner_kick_l":
            return True
    elif state.world_view.side == "r":
        if state.world_view.game_state == "corner_kick_r":
            return True

    return False

