# angle between c2 and c3 with vertex c1
import math
from math import atan2

from player.world import Coordinate


def angle_between(c1, c2, c3):
    angle = atan2(c3.pos_y - c1.pos_y, c3.pos_x - c1.pos_x) - atan2(c2.pos_y - c1.pos_y, c2.pos_x - c1.pos_x)
    if angle < 0:
        return math.radians(360) + angle
    return angle


# Calculates angle between two points (relative to the origin (0, 0))
def calculate_origin_angle_between(c1, c2):
    return atan2(c1.pos_y - c2.pos_y, c1.pos_x - c2.pos_x)


def _rotate_coordinate(coord, radians_to_rotate):
    new_x = math.cos(radians_to_rotate) * coord.pos_x - math.sin(radians_to_rotate) * coord.pos_y
    new_y = math.sin(radians_to_rotate) * coord.pos_x + math.cos(radians_to_rotate) * coord.pos_y
    return Coordinate(new_x, new_y)
