# angle between c2 and c3 with vertex c1
import math
from math import atan2

from player import world
from player.world import Coordinate


def angle_between(c1, c2, c3):
    angle = atan2(c3.pos_y - c1.pos_y, c3.pos_x - c1.pos_x) - atan2(c2.pos_y - c1.pos_y, c2.pos_x - c1.pos_x)
    if angle < 0:
        return math.radians(360) + angle
    return angle


# Calculates angle between two points (relative to the origin (0, 0))
def calculate_origin_angle_between(c1, c2):
    return atan2(c1.pos_y - c2.pos_y, c1.pos_x - c2.pos_x)


def rotate_coordinate(coord, radians_to_rotate):
    new_x = math.cos(radians_to_rotate) * coord.pos_x - math.sin(radians_to_rotate) * coord.pos_y
    new_y = math.sin(radians_to_rotate) * coord.pos_x + math.cos(radians_to_rotate) * coord.pos_y
    return Coordinate(new_x, new_y)


'''
- Returns the position of an object.
object_rel_angle is the relative angle to the observer (0 - 360)
distance is the distance from the observer to the object
my_x, my_y are the coordinates of the observer
my_angle is the global angle of the observer

Formular:
X= distance*cos(angle) +x0
Y= distance*sin(angle) +y0

example: 
My pos: x: -19,  y: -16 my_angle 0
(player Team1 9) 14.9 -7 0 0) = x:-4, y:-17,5
'''


def get_object_position(object_rel_angle: float, dist_to_obj: float, my_x: float, my_y: float,
                        my_global_angle: float):
    actual_angle = (my_global_angle + object_rel_angle) % 360
    x = dist_to_obj * math.cos(math.radians(actual_angle)) + my_x
    y = dist_to_obj * - math.sin(math.radians(actual_angle)) + my_y
    return world.Coordinate(x, y)

