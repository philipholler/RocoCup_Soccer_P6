import math

from geometry import calculate_smallest_origin_angle_between, calculate_full_circle_origin_angle
from player.player import PlayerState
from player.world import Coordinate


def jog_towards(player_state: PlayerState, target_position: Coordinate):
    minimum_last_update_time = player_state.now() - 10
    angle_known = player_state.player_angle.is_value_known(minimum_last_update_time)
    position_known = player_state.position.is_value_known(minimum_last_update_time)

    if not angle_known or not position_known:
        return orient_self()

    if not player_state.facing(target_position, 6) and player_state.last_turn_time < player_state.player_angle.last_updated_time:
        rotation = calculate_relative_angle(player_state, target_position)

        player_state.last_turn_time = player_state.now()
        return "(turn " + str(rotation) + ")"
    else:
        return "(dash 60)"


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


