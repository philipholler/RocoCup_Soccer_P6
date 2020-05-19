import math
from collections import deque
from itertools import islice
from math import sqrt, atan, degrees, exp

from constants import BALL_DECAY, KICKABLE_MARGIN
from geometry import is_angle_in_range, find_mean_angle, Coordinate, \
    calculate_full_origin_angle_radians, get_xy_vector, Vector2D, smallest_angle_difference, \
    inverse_y_axis, calculate_absolute_velocity
from utils import debug_msg


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
            return "(Precarious_data: value= {0}, last_updated_time= {1})".format(self.get_value(),
                                                                                  self.last_updated_time)
        else:
            return "(Precarious_data: unknown value)"

    def __repr__(self) -> str:
        if self.is_value_known():
            return "(Precarious_data: value= {0}, last_updated_time= {1})".format(str(self._value),
                                                                                  str(self.last_updated_time))
        else:
            return "(Precarious_data: unknown value)"


# ((player team? num?) Distance Direction DistChng? DirChng? BodyDir? HeadDir?)
class ObservedPlayer:
    def __init__(self, team, num, distance, direction, dist_chng, dir_chng, body_dir, head_dir, is_goalie,
                 coord, global_dir=None, observer_velocity: Vector2D = None) -> None:
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
        self.coord: Coordinate = coord
        self.velocity = calculate_absolute_velocity(observer_velocity, distance, global_dir, dist_chng, dir_chng)

    def __repr__(self) -> str:
        return "(team=" + str(self.team) + ", num=" + str(self.num) + ", distance=" + str(
            self.distance) + ", direction=" \
               + str(self.direction) + ", dist_chng=" + str(self.dist_chng) + ", dir_chng=" + str(self.dir_chng) \
               + ", body_dir=" + str(self.body_dir) + ", head_dir=" + str(self.head_dir) + ", is_goalie=" \
               + str(self.is_goalie) + ", coord=" + str(self.coord) + ")"

    def forecasted_position(self, ticks):
        if ticks == 0 or self.velocity is None or self.velocity.magnitude() <= 0.1:
            return self.coord

        return (self.coord.vector() + (self.velocity * ticks)).coord()


LOWER_FIELD_BOUND = Coordinate(-60, -40)
UPPER_FIELD_BOUND = Coordinate(60, 40)


class History:

    def __init__(self, max_size) -> None:
        self.list = deque([])
        self.max_size = max_size

    def add_data_point(self, element, time_stamp):
        self.list.appendleft((element, time_stamp))

        if len(self.list) > self.max_size:
            self.list.pop()  # Pop oldest element


class Ball:
    MAX_HISTORY_LEN = 10

    def __init__(self, distance: float, direction: int, dist_change, dir_change, global_dir, observer_velocity,
                 coord: Coordinate, now, velocity_history: History = History(MAX_HISTORY_LEN),
                 pos_history: History = History(MAX_HISTORY_LEN), dist_history: History = History(MAX_HISTORY_LEN)):
        super().__init__()
        self.distance = distance
        self.direction = direction
        self.global_dir = global_dir
        self.coord: Coordinate = coord
        self.dist_change = dist_change
        self.dir_change = dir_change

        self.position_history = pos_history
        self.dist_history = dist_history
        self.velocity_history = velocity_history

        calculated_vel = calculate_absolute_velocity(observer_velocity, distance, global_dir, dist_change, dir_change)
        self.absolute_velocity: Vector2D = self._get_average_absolute_velocity(calculated_vel, now)
        self.projection = None

        # Register current position, distance and velocity vector in history list
        self.position_history.add_data_point(coord, now)
        self.dist_history.add_data_point(distance, now)

        if self.absolute_velocity is not None:
            self.velocity_history.add_data_point(self.absolute_velocity, now)

    def approximate_position_direction_speed(self, minimum_data_points_used) -> (Coordinate, int, int):
        if self.projection is not None:
            return self.projection

        if len(self.position_history.list) <= 1:
            return None, None, None  # No information can be deduced about movement of ball
        history = self.position_history.list

        time_1 = history[0][1]
        time_2 = history[1][1]
        c1: Coordinate = history[0][0]
        c2: Coordinate = history[1][0]
        first_coord = c1
        last_coord = c2

        if time_1 == time_2 or c1.euclidean_distance_from(c2) < 0.1 or c1.euclidean_distance_from(c2) > 4.2:
            return c1, 0, 0

        final_speed = (c1.euclidean_distance_from(c2) / (time_1 - time_2)) * BALL_DECAY
        final_direction = degrees(calculate_full_origin_angle_radians(c1, c2))
        angles = [final_direction]  # Used for calculating 'average' angle

        max_deviation = 50  # angle deviation
        max_speed_deviation = 0.8
        age = time_1 - time_2
        max_age = 20

        def allowed_angle_deviation(index):
            return 90 if index == 0 else max_deviation

        previous_dist = final_speed
        data_points_used = 2
        for i, pos_and_time in enumerate(islice(history, 2, len(history))):
            c1 = c2
            c2 = pos_and_time[0]
            time_1 = time_2
            time_2 = pos_and_time[1]
            age += time_1 - time_2

            dist = c1.euclidean_distance_from(c2)
            if time_1 == time_2 or dist <= 0.05 or (dist < 0.3 and previous_dist < 0.3) or dist > 4.2:
                break
            previous_dist = dist

            # calculate angle from point observed 2 ticks prior
            direction = degrees(calculate_full_origin_angle_radians(history[i][0], c2))
            direction_similar = is_angle_in_range(direction, (final_direction - allowed_angle_deviation(i)) % 360,
                                                  (final_direction + allowed_angle_deviation(i)) % 360)

            speed = (dist / (time_1 - time_2)) * pow(BALL_DECAY, age)
            speed_similar = (final_speed - max_speed_deviation) <= speed <= (final_speed + max_speed_deviation)

            if direction_similar and speed_similar and age < max_age:
                data_points_used += 1
                last_coord = c2
                angles.append(degrees(calculate_full_origin_angle_radians(first_coord, c2)))
                final_speed = (final_speed * age + speed) / (age + 1)  # calculate average with new value
                final_direction = find_mean_angle(angles, 179)
            else:
                debug_msg("Previous points did not match. Speed : " + str(speed) + "vs." + str(
                    final_speed) + "| Direction :" + str(direction) +
                          "vs." + str(final_direction) + "| age: " + str(age) + str(c1) + str(c2), "POSITIONAL")
                break  # This vector did not fit projection, so no more history is used in the projection

        if data_points_used < minimum_data_points_used:
            return None, None, None

        debug_msg("Prediction based on {0} of these data points: {1}".format(data_points_used, self.position_history)
                  , "INTERCEPTION")

        direction = degrees(calculate_full_origin_angle_radians(first_coord, last_coord))
        self.projection = self.position_history.list[0][0], direction, final_speed
        return self.position_history.list[0][0], direction, final_speed

    def project_position_in_n_ticks(self, ticks):
        positions = self.project_ball_position(ticks, ticks - 1)
        if positions is None:
            return None
        return positions[len(positions) - 1]

    def project_ball_position(self, ticks: int, offset: int):
        positions = []
        # coord, direction, speed = self.approximate_position_direction_speed(minimum_data_points)

        if self.absolute_velocity is None:
            return None  # No prediction can be made

        def advance(previous_location: Coordinate, vel_vector: Vector2D):
            return Coordinate(previous_location.pos_x + vel_vector.x, previous_location.pos_y + vel_vector.y)

        velocity = self.absolute_velocity.decayed(BALL_DECAY, 1)
        positions.append(advance(self.coord, self.absolute_velocity))

        for i in range(1, ticks + offset):
            velocity = velocity.decayed(BALL_DECAY, 1)
            positions.append(advance(positions[i - 1], velocity))

        return positions[offset:]

    def project_ball_position_vector_method(self, ticks: int, offset: int, minimum_data_points=4):
        """positions = []

        if direction is None:
            return None  # No prediction can be made

        def advance(previous_location: Coordinate, vx, vy):
            return Coordinate(previous_location.pos_x + vx, previous_location.pos_y + vy)

        velocity = get_xy_vector(direction=-direction, length=speed)
        positions.append(advance(coord, velocity.pos_x, velocity.pos_y))

        for i in range(1, ticks + offset):
            velocity *= BALL_DECAY
            positions.append(advance(positions[i - 1], velocity.pos_x, velocity.pos_y))

        return positions[offset:]"""
        pass

    def will_hit_goal_within(self, ticks):
        ball_positions = self.project_ball_position(ticks, 0)
        if ball_positions is None:
            return False
        for position in ball_positions:
            if position.pos_x <= -52.5 and -7.01 <= position.pos_y <= 7.01:
                return True
        return False

    def get_goal_hit_coordinate(self, ticks):
        ball_positions = self.project_ball_position(ticks, 0)
        if ball_positions is None:
            return None
        for position in ball_positions:
            pos, dire, speed = self.approximate_position_direction_speed(3)
            if position.pos_x - speed <= -52.5 and -7.01 <= position.pos_y <= 7.01:
                return position
        return None

    def project_ball_collision_time(self):
        start_time = self.dist_history.list[0][1]
        start_dist = self.dist_history.list[0][0]
        previous_dist = start_dist
        previous_tick = start_time
        avg_speed = 0

        for i, (dist, tick) in enumerate(islice(self.dist_history.list, 1, len(self.dist_history.list))):
            dist_delta = dist - previous_dist
            time_delta = previous_tick - tick

            age = start_time - tick

            if time_delta == 0:
                break

            speed = dist_delta / time_delta
            if speed < 0.1:
                break  # Ball is not rolling in same direction (or only insignificantly so)

            projected_speed = speed * exp((BALL_DECAY - 1) * age)  # V = V0 * e^(0.06*t)
            avg_speed = (i * avg_speed + projected_speed) / (i + 1)

            previous_dist = dist
            previous_tick = tick

        if avg_speed <= 0:
            return None

        dist_left = start_dist
        ticks_until_collision = 0
        while dist_left > KICKABLE_MARGIN - 0.1:
            dist_left -= avg_speed
            avg_speed *= BALL_DECAY
            ticks_until_collision += 1
            if ticks_until_collision > 10:
                return None

        return start_time + ticks_until_collision

    def project_ball_collision_time_2(self, player_coord, time):
        offset = time - self.position_history.list[0][1]
        positions: [Coordinate] = self.project_ball_position(5, offset)
        if positions is not None:
            for i, pos in enumerate(positions):
                if pos.euclidean_distance_from(player_coord) < KICKABLE_MARGIN - 0.1:
                    return time + i
        return None

    def __repr__(self) -> str:
        return "(distance= {0}, direction= {1}, coord= {2})".format(
            self.distance, self.direction, self.coord)

    def __str__(self) -> str:
        return "(distance= {0}, direction= {1}, coord= {2})".format(
            self.distance, self.direction, self.coord)

    def is_moving_closer(self):
        if len(self.dist_history.list) < 2:
            return False

        return self.dist_history.list[0][0] < self.dist_history.list[1][0]

    def _get_average_absolute_velocity(self, calculated_velocity, now):
        if calculated_velocity is None:
            return None

        current_velocity = calculated_velocity
        if current_velocity.magnitude() < 0.09:
            return Vector2D(0, 0)

        if current_velocity.magnitude() < 0.14:
            return current_velocity * 0.5

        avg_magnitude = current_velocity.magnitude() * 1.4
        avg_direction_delta = 0
        total_weight = 1.4
        previous_time = now
        points_used = 0

        for i, velocity_and_time in enumerate(self.velocity_history.list):
            velocity = velocity_and_time[0]
            time = velocity_and_time[1]

            if velocity.magnitude() < 0.05:
                break

            weight = max(1.0, (1.4 - (i + 1) * 0.1))
            time_delta = previous_time - time
            projected_velocity: Vector2D = velocity.decayed(BALL_DECAY, now - time)

            angle_delta = smallest_angle_difference(from_angle=current_velocity.direction(),
                                                    to_angle=projected_velocity.direction())
            speed_delta = projected_velocity.magnitude() - current_velocity.magnitude()
            MAX_ANGLE_DELTA = 8
            MAX_SPEED_DELTA = 0.3
            MAX_TIME_DELTA = 7

            if abs(angle_delta) > MAX_ANGLE_DELTA or abs(speed_delta) > MAX_SPEED_DELTA or time_delta > MAX_TIME_DELTA:
                ##print("DELTA TOO BIG. Angle: ", angle_delta, "| Speed:", speed_delta, "time delta", time_delta)
                break

            avg_magnitude += projected_velocity.magnitude() * weight
            avg_direction_delta += angle_delta * weight
            total_weight += weight
            points_used += 1

        avg_magnitude /= total_weight
        avg_direction_delta /= total_weight
        avg_direction = (current_velocity.direction() + avg_direction_delta) % 360
        final_projection = Vector2D.velocity_to_xy(velocity=avg_magnitude, degrees=avg_direction)

        """print("HISTORY (used {0}): ".format(points_used), list(map(lambda v: v[0].world_direction(), self.velocity_history.list)))
        print("HISTORY (used {0}): ".format(points_used), list(map(lambda v: v[0].magnitude(), self.velocity_history.list)))
        print("AVERAGE vector:", final_projection, "| angle: ", final_projection.world_direction(), "| speed:", final_projection.magnitude())
"""
        return final_projection

    def relative_ball_position_vector(self):
        rel_x = self.distance * math.cos(math.radians(self.global_dir))
        rel_y = self.distance * math.sin(math.radians(self.global_dir))
        return Vector2D(rel_x, -rel_y)


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
