import math

from geometry import calculate_smallest_origin_angle_between, calculate_full_circle_origin_angle
from player.player import PlayerState
from player.world import Coordinate


def jog_towards(player_state: PlayerState, target_position: Coordinate):

    if not player_state.position.is_value_known() or not player_state.player_angle.is_value_known(player_state.world_view.sim_time - 5):
        return orient_self()

    # delta angle should depend on how close the player is to the target
    if not player_state.facing(target_position, 4):
        rotation = calculate_full_circle_origin_angle(target_position, player_state.position.get_value())
        rotation = math.degrees(rotation)
        rotation -= player_state.player_angle.get_value()

        # Pick the short way around (<180 degrees)
        if rotation > 180:
            rotation -= 360
        elif rotation < -180:
            rotation += 360
        return "(turn " + str(rotation * 0.8) + ")"
    else:
        return "(dash 65)"


def orient_self():
    return "(turn 15)"
