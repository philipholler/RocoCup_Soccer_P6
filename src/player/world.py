from math import sqrt


class World:

    def __init__(self) -> None:
        super().__init__()
        self.other_players = [Player]


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


# ((player team? num?) Distance Direction DistChng? DirChng? BodyDir? HeadDir?)
class Player:
    def __init__(self, team, num, distance, direction, dist_chng, dir_chng, body_dir, head_dir, coord) -> None:
        super().__init__()
        self.team = team
        self.num = num
        self.distance = distance
        self.direction = direction
        self.dist_chng = dist_chng
        self.dir_chng = dir_chng
        self.body_dir = body_dir
        self.head_dir = head_dir
        self.coord = coord

    def __repr__(self) -> str:
        return "(team=" + str(self.team) + ", num=" + str(self.num) + ", distance=" + str(self.distance) + ", direction=" \
               + str(self.direction) + ", dist_chng=" + str(self.dist_chng) + ", dir_chng=" + str(self.dir_chng) \
               + ", body_dir=" + str(self.body_dir) + ", head_dir=" + str(self.head_dir) + ", coord=" + str(self.coord) \
               + ")"

LOWER_FIELD_BOUND = Coordinate(-60, -40)
UPPER_FIELD_BOUND = Coordinate(60, 40)


def is_inside_field_bounds(coordinate: Coordinate):
    below_upper_bounds = coordinate <= UPPER_FIELD_BOUND
    above_lower_bounds = coordinate >= LOWER_FIELD_BOUND
    return below_upper_bounds and above_lower_bounds
