import math

from geometry import calculate_origin_angle_between
from player.world import Coordinate


def jog_towards(player_state, target_position: Coordinate):
    if not player_state.position.is_value_known() or not player_state.player_angle.is_value_known():
        return orient_self()

    # delta angle should depend on how close the player is to the target
    if not player_state.facing(target_position, math.radians(5)):
        rotation = calculate_origin_angle_between(player_state.position.get_value(), target_position)
        rotation -= player_state.player_angle.get_value()
        return "(turn " + str(4) + ")"
    else:
        return "(dash 65)"


def orient_self():
    return "(turn 15)"
