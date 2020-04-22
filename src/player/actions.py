import math

from geometry import calculate_smallest_origin_angle_between, calculate_full_circle_origin_angle, \
    get_distance_between_coords
from player.player import PlayerState
from player.world_objects import Coordinate, ObservedPlayer

MAXIMUM_KICK_DISTANCE = 1
ORIENTATION_ACTIONS = ["(turn_neck 90)", "(turn_neck -180)", "(turn 180)", "(turn_neck 90)"]
NECK_ORIENTATION_ACTIONS = ["(turn_neck 90)", "(turn_neck -180)", "(turn_neck 90)"]

VIEW_RESET = "(change_view normal high)"


def reset_neck(state):
    return "(turn_neck " + str(-state.body_state.neck_angle) + ")"


def jog_towards(state: PlayerState, target_position: Coordinate):
    actions = []
    history = state.action_history
    minimum_last_update_time = state.now() - 10
    angle_known = state.body_angle.is_value_known(minimum_last_update_time)
    position_known = state.position.is_value_known(minimum_last_update_time)

    if not angle_known or not position_known:
        return orient_self(state)

    if not state.body_facing(target_position, 6) and history.last_turn_time < state.body_angle.last_updated_time:
        if state.team_name == "Team1" and state.num == 2:
            print(str(state.body_angle.get_value()))

        rotation = calculate_relative_angle(state, target_position)

        history.last_turn_time = state.now()
        actions.append("(turn " + str(rotation) + ")")
    else:
        actions.append("(dash 60)")

    actions.append(orient_self_neck_only(state))
    return actions


def jog_towards_ball(state: PlayerState):
    minimum_last_update_time = state.now() - 10
    ball_known = state.world_view.ball.is_value_known(minimum_last_update_time)

    if not ball_known:
        return orient_self(state)

    return jog_towards(state, state.world_view.ball.get_value().coord)


def choose_rand_player(player_passing : PlayerState):
    if len(player_passing.world_view.other_players) != 0:
        return player_passing.world_view.other_players[0]
    return None


def get_player(target_player_num, team_name, state: PlayerState):
    for p in state.world_view.other_players:
        if p.num is not None and int(p.num) == target_player_num and p.team == team_name:
            return p


def pass_ball_to(target_player_num, state: PlayerState):
    world = state.world_view

    if world.ball.is_value_known(world.ticks_ago(5)) and state.position.is_value_known(world.ticks_ago(5)):
        ball = world.ball.get_value()
        if ball.coord.euclidean_distance_from(state.position.get_value()) < MAXIMUM_KICK_DISTANCE:
            target = get_player(target_player_num, state.team_name, state)
            if target is not None:
                return "(kick " + str(calculate_power(target.distance)) + " " + str(target.direction) + ")"
            else:
                return orient_self(state)
        else:
            return jog_towards_ball(state)
    else:
        orient_self(state)


def pass_ball_to_random(player_passing: PlayerState):
    target: ObservedPlayer = choose_rand_player(player_passing)
    if target is None:
        return orient_self(player_passing)

    direction = target.direction
    power = calculate_power(target.distance)

    return "(kick " + str(power) + " " + str(direction) + ")"


def kick_to_goal(player : PlayerState):
    if player.team_name == "Team1":
        target = Coordinate(53.0, 0)
    else:
        target = Coordinate(-53.0, 0)

    direction = calculate_relative_angle(player, target)

    return "(kick " + str(160) + " " + str(direction) + ")"


def orient_self(state: PlayerState):
    history = state.action_history
    action = ORIENTATION_ACTIONS[history.last_orientation_action]
    history.last_orientation_action += 1
    history.last_orientation_action %= len(ORIENTATION_ACTIONS)
    return action


def orient_self_neck_only(state: PlayerState):
    history = state.action_history
    if history.last_orientation_action >= len(NECK_ORIENTATION_ACTIONS):
        # Reset neck position
        history.last_orientation_action = 0
        return reset_neck(state)

    action = NECK_ORIENTATION_ACTIONS[history.last_orientation_action]
    history.last_orientation_action += 1
    return action


def calculate_relative_angle(player_state, target_position):
    rotation = calculate_full_circle_origin_angle(target_position, player_state.position.get_value())
    rotation = math.degrees(rotation)
    rotation -= player_state.body_angle.get_value()

    # Pick the short way around (<180 degrees)
    if rotation > 180:
        rotation -= 360
    elif rotation < -180:
        rotation += 360

    return rotation


# TODO: find out how to calculate power from distance
def calculate_power(distance):
    return float(distance) * 3


