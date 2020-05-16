# angle between c2 and c3 with vertex c1
import math
from math import atan2


class Coordinate:
    def __init__(self, pos_x: float, pos_y: float):
        self.pos_x: float = pos_x
        self.pos_y: float = pos_y

    def __repr__(self):
        return "(" + str(self.pos_x) + ", " + str(self.pos_y) + ")"

    def __add__(self, other):
        return Coordinate(self.pos_x + other.pos_x, self.pos_y + other.pos_y)

    def __sub__(self, other):
        return Coordinate(self.pos_x - other.pos_x, self.pos_y - other.pos_y)

    def __mul__(self, factor):
        return Coordinate(self.pos_x * factor, self.pos_y * factor)

    def __le__(self, other):
        return self.pos_x <= other.pos_x and self.pos_y <= other.pos_y

    def __lt__(self, other):
        return self.pos_x < other.pos_x and self.pos_y < other.pos_y

    def __ge__(self, other):
        return self.pos_x >= other.pos_x and self.pos_y >= other.pos_y

    def __gt__(self, other):
        return self.pos_x > other.pos_x and self.pos_y > other.pos_y

    def euclidean_distance_from(self, other):
        return math.sqrt((self.pos_x - other.pos_x) ** 2 + (self.pos_y - other.pos_y) ** 2)

    def vector(self):
        return Vector2D(self.pos_x, self.pos_y)


def angle_between(c1, c2, c3):
    angle = atan2(c3.pos_y - c1.pos_y, c3.pos_x - c1.pos_x) - atan2(c2.pos_y - c1.pos_y, c2.pos_x - c1.pos_x)
    if angle < 0:
        return math.radians(360) + angle
    return angle


# Calculates angle between two points (relative to the origin (0, 0))
def calculate_smallest_origin_angle_between(c1, c2):
    angle = atan2(c1.pos_y - c2.pos_y, c1.pos_x - c2.pos_x)
    return angle


# Calculates the angle (0-6.24 radians) from due east to c1 relative to c2
def calculate_full_origin_angle_radians(c1, c2):
    angle = atan2(c1.pos_y - c2.pos_y, c1.pos_x - c2.pos_x)

    # Turn negative angles into positive angles
    if angle < 0:
        angle += math.radians(360)

    # RoboCup inverts angles with respect to regular geometric functions (ie. clockwise is positive)
    return math.radians(360) - angle


def rotate_coordinate(coord, radians_to_rotate):
    new_x = math.cos(radians_to_rotate) * coord.pos_x - math.sin(radians_to_rotate) * coord.pos_y
    new_y = math.sin(radians_to_rotate) * coord.pos_x + math.cos(radians_to_rotate) * coord.pos_y
    return Coordinate(new_x, new_y)


def smallest_angle_difference(to_angle, from_angle):
    a = to_angle - from_angle
    return (a + 180) % 360 - 180


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
    return Coordinate(x, y)


def get_distance_between_coords(c1, c2):
    x = c2.pos_x - c1.pos_x
    y = c2.pos_y - c1.pos_y
    return math.sqrt(pow(x, 2) + pow(y, 2))


def is_angle_in_range(angle, from_angle, to_angle):
    if from_angle > to_angle:  # Case where range wraps around 360
        return from_angle < angle <= 360 or 0 <= angle <= to_angle

    return from_angle <= angle <= to_angle


def get_xy_vector(direction, length):
    radians = math.radians(direction)
    return Coordinate(length * math.cos(radians), length * math.sin(radians))


# Note there is no standard definition for averaging angles
def find_mean_angle(angles, acceptable_variance=3.0):
    if len(angles) == 0:
        return None

    if len(angles) == 1:
        return angles[0]

    # We expect more than half of the angles to be close together (eliminate outliers)
    expected_close_angles = int(len(angles) / 2 + 1)
    best_angle_so_far = 0
    best_cluster_size = 0

    for i, first_angle in enumerate(angles):
        differences = [0]
        for other_angle in angles[i + 1:]:
            difference = smallest_angle_difference(from_angle=first_angle, to_angle=other_angle)
            if abs(difference) <= acceptable_variance:
                differences.append(difference)

        if len(differences) >= expected_close_angles:
            return (first_angle + average(differences)) % 360

        if len(differences) > best_cluster_size:
            best_angle_so_far = (first_angle + average(differences)) % 360
            best_cluster_size = len(differences)

    # No angles were close enough to provide a non-ambiguous solution
    if best_cluster_size <= 1:
        return None

    return best_angle_so_far


# Note that the mean value of angles is not well defined (fx. what is the mean angle of (0, 90, 180, 270)?)
# This function averages angles that are close together.
def average(numbers):
    return sum(numbers) / len(numbers)


class Vector2D:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)

    @staticmethod
    def velocity_to_xy(velocity, degrees):
        x = math.cos(math.radians(degrees)) * velocity
        y = math.sin(math.radians(degrees)) * velocity
        return Vector2D(x, y)

    def direction(self):
        if self.x == 0:
            return 90 if self.y >= 0 else -90
        return math.degrees(math.atan2(self.y, self.x)) % 360

    def world_direction(self):
        return 360 - math.degrees(math.atan2(self.y, self.x)) % 360

    def magnitude(self):
        return math.sqrt(self.x ** 2 + self.y ** 2)

    def rotated(self, radians):
        x2 = self.x * math.cos(radians) - self.y * math.sin(radians)
        y2 = self.x * math.sin(radians) + self.y * math.cos(radians)
        return Vector2D(x2, y2)

    def decayed(self, decay_rate, ticks=1):
        total_decay = decay_rate ** ticks
        return Vector2D(self.x * total_decay, self.y * total_decay)

    def distance_from(self, other):
        return math.sqrt(((self.x - other.x) ** 2) + ((self.y - other.y) ** 2))

    def extend_length_to(self, new_length):
        factor = new_length / self.magnitude()
        return self * factor

    def coord(self):
        return Coordinate(self.x, self.y)

    def __add__(self, other):
        return Vector2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vector2D(self.x - other.x, self.y - other.y)

    def __repr__(self) -> str:
        return "(" + str(self.x) + ", " + str(self.y) + ")"

    def __mul__(self, factor):
        return Vector2D(self.x * factor, self.y * factor)


def inverse_y_axis(degrees):
    return (360 - degrees) % 360


def calculate_absolute_velocity(observer_velocity: Vector2D, distance, global_dir, dist_change, dir_change):
    if dir_change is None or dist_change is None or observer_velocity is None:
        return None

    # First calculate relative velocity
    rel_velocity_x = dist_change
    rel_velocity_y = (-math.radians(dir_change)) * distance
    relative_velocity_vector = Vector2D(rel_velocity_x, rel_velocity_y)
    rel_speed = relative_velocity_vector.magnitude()

    # Rotate to match our coordinate system
    velocity_angle = (math.radians(inverse_y_axis(global_dir)) + math.atan2(rel_velocity_y, rel_velocity_x))
    rel_velocity_x = rel_speed * math.cos(velocity_angle)
    rel_velocity_y = rel_speed * math.sin(velocity_angle)

    # Add observer velocity to relative velocity to get absolute velocity
    return observer_velocity + Vector2D(rel_velocity_x, rel_velocity_y)
