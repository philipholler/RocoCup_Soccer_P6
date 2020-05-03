from collections import deque
from itertools import islice
from math import sqrt, atan, degrees

from constants import BALL_DECAY
from geometry import is_angle_in_range, find_mean_angle, Coordinate, \
    calculate_full_origin_angle_radians, get_xy_vector


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

    def is_value_known(self, last_update_time_minimum=0):
        return self._value is not None and self.last_updated_time >= last_update_time_minimum

    def set_value_unknown(self):
        self._value = None

    def __str__(self) -> str:
        if self.is_value_known():
            return "(Precarious_data: value= {0}, last_updated_time= {1})".format(self.get_value(), self.last_updated_time)
        else:
            return "(Precarious_data: unknown value)"

    def __repr__(self) -> str:
        if self.is_value_known():
            return "(Precarious_data: value= {0}, last_updated_time= {1})".format(str(self._value), str(self.last_updated_time))
        else:
            return "(Precarious_data: unknown value)"


# ((player team? num?) Distance Direction DistChng? DirChng? BodyDir? HeadDir?)
class ObservedPlayer:
    def __init__(self, team, num, distance, direction, dist_chng, dir_chng, body_dir, head_dir, is_goalie,
                 coord) -> None:
        super().__init__()
        self.team = team
        self.num = num
        self.distance = distance
        self.direction = direction
        self.dist_chng = dist_chng
        self.dir_chng = dir_chng
        self.body_dir = body_dir
        self.head_dir = head_dir
        self.is_goalie = is_goalie
        self.coord = coord

    def __repr__(self) -> str:
        return "(team=" + str(self.team) + ", num=" + str(self.num) + ", distance=" + str(
            self.distance) + ", direction=" \
               + str(self.direction) + ", dist_chng=" + str(self.dist_chng) + ", dir_chng=" + str(self.dir_chng) \
               + ", body_dir=" + str(self.body_dir) + ", head_dir=" + str(self.head_dir) + ", is_goalie=" \
               + str(self.is_goalie) + ", coord=" + str(self.coord) + ")"


LOWER_FIELD_BOUND = Coordinate(-60, -40)
UPPER_FIELD_BOUND = Coordinate(60, 40)


class Ball:
    MAX_HISTORY_LEN = 8

    def __init__(self, distance: float, direction: int, coord: Coordinate, time, pos_history: deque=None) -> None:
        super().__init__()
        self.distance = distance
        self.direction = direction
        self.coord: Coordinate = coord
        if pos_history is None:
            self.position_history: deque = deque([])
        else:
            self.position_history: deque = pos_history

        self.position_history.appendleft((coord, time))
        if len(self.position_history) > self.MAX_HISTORY_LEN:
            self.position_history.pop()  # Pop oldest element

    def approximate_position_direction_speed(self, minimum_data_points_used) -> (Coordinate, int, int):
        if len(self.position_history) <= 1:
            return None, None, None  # No information can be deduced about movement of ball
        history = self.position_history

        time_1 = history[0][1]
        time_2 = history[1][1]
        c1: Coordinate = history[0][0]
        c2: Coordinate = history[1][0]
        first_coord = c1
        last_coord = c2

        if time_1 == time_2 or c1.euclidean_distance_from(c2) < 0.1:
            return c1, 0, 0

        final_speed = (c1.euclidean_distance_from(c2) / (time_1 - time_2)) * BALL_DECAY
        final_direction = degrees(calculate_full_origin_angle_radians(c1, c2))
        angles = [final_direction]  # Used for calculating 'average' angle

        max_deviation = 60  # angle deviation
        max_speed_deviation = 1.2
        age = time_1 - time_2
        max_age = 12

        data_points_used = 2
        for i, pos_and_time in enumerate(islice(history, 2, len(history))):
            c1 = c2
            c2 = pos_and_time[0]
            time_1 = time_2
            time_2 = pos_and_time[1]

            if time_1 == time_2 or c1.euclidean_distance_from(c2) < 0.05:
                break

            age += time_1 - time_2
            speed = (c1.euclidean_distance_from(c2) / (time_1 - time_2)) * pow(BALL_DECAY, age)
            direction = degrees(calculate_full_origin_angle_radians(c1, c2))
            print("direction", direction, "finaldir: ", final_direction)
            direction_similar = is_angle_in_range(direction, (final_direction - max_deviation) % 360,
                                                  (final_direction + max_deviation) % 360)
            speed_similar = (final_speed - max_speed_deviation) <= speed <= (final_speed + max_speed_deviation)

            if direction_similar and speed_similar and age < max_age:
                data_points_used += 1
                last_coord = c2
                angles.append(direction)
                final_speed = (final_speed * age + speed) / (age + 1)  # calculate average with new value
                final_direction = find_mean_angle(angles, max_deviation)
            else:
                print("Previous points did not match. Speed : ", speed, "vs.", final_speed, "| Direction :", direction, "vs.", final_direction, "| age: ", age, c1, c2)
                break  # This vector did not fit projection, so no more history is used in the projection

        if data_points_used < minimum_data_points_used:
            return None, None, None
        print("Prediction based on {0} data points".format(data_points_used))
        return self.position_history[0][0], degrees(calculate_full_origin_angle_radians(first_coord, last_coord)), final_speed

    def project_ball_position(self, ticks: int, offset: int):
        positions = []
        coord, direction, speed = self.approximate_position_direction_speed(minimum_data_points_used=4)

        if direction is None:
            return None  # No prediction can be made

        def advance(previous_location: Coordinate, vx, vy):
            return Coordinate(previous_location.pos_x + vx, previous_location.pos_y + vy)

        velocity = get_xy_vector(direction=-direction, length=speed)
        positions.append(advance(coord, velocity.pos_x, velocity.pos_y))

        for i in range(1, ticks + offset):
            velocity *= BALL_DECAY
            positions.append(advance(positions[i - 1], velocity.pos_x, velocity.pos_y))

        return positions[offset:]





    def __repr__(self) -> str:
        return "(distance= {0}, direction= {1}, dist_chng= {2}, dir_chng= {3}, coord= {4}, last_pos= {5}, last_pos_2= {6})".format(self.distance, self.direction, self.dist_chng, self.dir_chng, self.coord
                                                                       , self.last_position, self.last_position_2)
    def __str__(self) -> str:
        return "(distance= {0}, direction= {1}, dist_chng= {2}, dir_chng= {3}, coord= {4}, last_pos= {5}, last_pos_2= {6})".format(self.distance, self.direction, self.dist_chng, self.dir_chng, self.coord
                                                        , self.last_position, self.last_position_2)




class Goal:
    def __init__(self, goal_side, distance, relative_angle) -> None:
        super().__init__()
        self.goal_side = goal_side
        self.distance = distance
        self.relative_angle = relative_angle

    def __repr__(self) -> str:
        return "(goal_side=" + str(self.goal_side) + ", distance to goal=" + \
               str(self.distance) + ", relative_angle=" + str(self.relative_angle) + ")"


class Line:
    def __init__(self, line_side, distance, relative_angle) -> None:
        super().__init__()
        self.line_side = line_side
        self.distance = distance
        self.relative_angle = relative_angle

    def __repr__(self) -> str:
        return "(line_side=" + str(self.line_side) + ", distance to line=" + \
               str(self.distance) + ", relative_angle=" + str(self.relative_angle) + ")"


def is_inside_field_bounds(coordinate: Coordinate):
    below_upper_bounds = coordinate <= UPPER_FIELD_BOUND
    above_lower_bounds = coordinate >= LOWER_FIELD_BOUND
    return below_upper_bounds and above_lower_bounds
