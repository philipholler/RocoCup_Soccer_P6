from math import sqrt


class Coordinate:
    def __init__(self, pos_x, pos_y):
        self.pos_x = pos_x
        self.pos_y = pos_y

    def __repr__(self):
        return "(" + str(self.pos_x) + ", " + str(self.pos_y) + ")"

    def __add__(self, other):
        return Coordinate(self.pos_x + other.pos_x, self.pos_y + other.pos_y)

    def __sub__(self, other):
        return Coordinate(self.pos_x - other.pos_x, self.pos_y - other.pos_y)

    def __le__(self, other):
        return self.pos_x <= other.pos_x and self.pos_y <= other.pos_y

    def __lt__(self, other):
        return self.pos_x < other.pos_x and self.pos_y < other.pos_y

    def __ge__(self, other):
        return self.pos_x >= other.pos_x and self.pos_y >= other.pos_y

    def __gt__(self, other):
        return self.pos_x > other.pos_x and self.pos_y > other.pos_y

    def euclidean_distance_from(self, other):
        return sqrt((self.pos_x - other.pos_x) ** 2 + (self.pos_y - other.pos_y) ** 2)


class PrecariousData:
    def __init__(self, initial_value, initial_time):
        self._value = initial_value
        self.last_updated_time = initial_time

    @classmethod
    def unknown(cls):
        return cls(None, 0)

    def set_value(self, new_value, current_time):
        self._value = new_value
        self.last_updated_time = current_time

    def get_value(self):
        return self._value

    def is_value_known(self):
        return self._value is not None

    def set_value_unknown(self):
        self._value = None


LOWER_FIELD_BOUND = Coordinate(-60, -40)
UPPER_FIELD_BOUND = Coordinate(60, 40)


def is_inside_field_bounds(coordinate: Coordinate):
    below_upper_bounds = coordinate <= UPPER_FIELD_BOUND
    above_lower_bounds = coordinate >= LOWER_FIELD_BOUND
    return below_upper_bounds and above_lower_bounds
