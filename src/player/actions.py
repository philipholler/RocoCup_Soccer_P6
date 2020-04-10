import math

from geometry import calculate_smallest_origin_angle_between, calculate_full_circle_origin_angle, \
    get_distance_between_coords
from player.player import PlayerState
from player.world import Coordinate


def jog_towards(player_state: PlayerState, target_position: Coordinate):
    minimum_last_update_time = player_state.now() - 10
    angle_known = player_state.player_angle.is_value_known(minimum_last_update_time)
    position_known = player_state.position.is_value_known(minimum_last_update_time)

    if not angle_known or not position_known:
        return orient_self()

    if not player_state.facing(target_position,
                               6) and player_state.last_turn_time < player_state.player_angle.last_updated_time:
        rotation = calculate_full_circle_origin_angle(target_position, player_state.position.get_value())
        rotation = math.degrees(rotation)
        rotation -= player_state.player_angle.get_value()

        # Pick the short way around (<180 degrees)
        if rotation > 180:
            rotation -= 360
        elif rotation < -180:
            rotation += 360

        player_state.last_turn_time = player_state.now()
        return "(turn " + str(rotation) + ")"
    else:
        return "(dash 60)"


def jog_towards_ball(player_state: PlayerState):
    minimum_last_update_time = player_state.now() - 10
    ball_known = player_state.world_view.ball.is_value_known(minimum_last_update_time)

    if not ball_known:
        return orient_self()

    return jog_towards(player_state, player_state.world_view.ball.coord)


def pass_ball_to(player_passing: PlayerState, player_receiving: PlayerState):
    minimum_last_update_time = player_passing.now() - 10
    angle_known = player_passing.player_angle.is_value_known(minimum_last_update_time)
    position_passing = player_passing.position.is_value_known(minimum_last_update_time)
    minimum_last_update_time = player_receiving.now() - 10
    position_receiver = player_receiving.position.is_value_known(minimum_last_update_time)

    if not angle_known or not position_passing or not position_receiver:
        return orient_self()

    direction = calculate_relative_angle(player_passing, player_receiving.position.get_value())
    power = calculate_power(get_distance_between_coords(player_passing.position.get_value(),
                                                        player_receiving.position.get_value()))

    return "(kick " + str(power) + " " + str(direction) + ")"


def orient_self():
    return "(turn 45)"


def calculate_relative_angle(player_state, target_position):
    rotation = calculate_full_circle_origin_angle(target_position, player_state.position.get_value())
    rotation = math.degrees(rotation)
    rotation -= player_state.player_angle.get_value()

    # Pick the short way around (<180 degrees)
    if rotation > 180:
        rotation -= 360
    elif rotation < -180:
        rotation += 360

    return rotation


# TODO: find out how to calculate power from distance
def calculate_power(distance):
    return 60
