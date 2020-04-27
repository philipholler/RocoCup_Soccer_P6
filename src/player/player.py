import math

import constants
import geometry
from constants import BALL_DECAY, KICKABLE_MARGIN
from geometry import calculate_full_circle_origin_angle
from player.world_objects import PrecariousData, Coordinate, ObservedPlayer, Ball

MAX_MOVE_DISTANCE_PER_TICK = 1.05
APPROA_GOAL_DISTANCE = 30


class PlayerState:

    def __init__(self):
        self.team_name = ""
        self.num = -1
        self.player_type = None
        self.position: PrecariousData = PrecariousData.unknown()
        self.world_view = WorldView(0)
        self.body_angle: PrecariousData = PrecariousData.unknown()
        self.action_history = ActionHistory()
        self.body_state = BodyState()
        self.players_close_behind = 0
        self.coach_command = PrecariousData.unknown()
        self.starting_position: Coordinate = None
        self.playing_position: Coordinate = None
        self.last_see_update = 0
        super().__init__()

    def __str__(self) -> str:
        return "side: {0}, team_name: {1}, player_num: {2}, position: {3}".format(self.world_view.side, self.team_name
                                                                                  , self.num, self.position)

    def is_approaching_goal(self):
        if self.position.is_value_known():
            pos: Coordinate = self.position.get_value()
            if self.world_view.side == "l" and pos.euclidean_distance_from(Coordinate(52.5, 0)) < APPROA_GOAL_DISTANCE:
                return True
            if self.world_view.side == "r" and pos.euclidean_distance_from(Coordinate(-52.5, 0)) < APPROA_GOAL_DISTANCE:
                return True
        return False

    def get_global_start_pos(self):
        if self.world_view.side == "l":
            return Coordinate(self.starting_position.pos_x, -self.starting_position.pos_y)
        else:
            return Coordinate(-self.starting_position.pos_x, self.starting_position.pos_y)

    def get_global_play_pos(self):
        if self.world_view.side == "l":
            return Coordinate(self.playing_position.pos_x, -self.playing_position.pos_y)
        else:
            return Coordinate(-self.playing_position.pos_x, self.playing_position.pos_y)

    def get_global_angle(self):
        if self.body_angle.is_value_known():
            neck_angle = self.body_state.neck_angle
            return PrecariousData(self.body_angle.get_value() + neck_angle, self.body_angle.last_updated_time)
        else:
            return PrecariousData.unknown()

    def body_facing(self, coordinate, delta):
        if not self.body_angle.is_value_known() or not self.position.is_value_known():
            # should this return unknown?(None?)
            return False

        expected_angle = math.degrees(calculate_full_circle_origin_angle(coordinate, self.position.get_value()))
        return abs(geometry.smallest_angle_difference(expected_angle, self.body_angle.get_value())) < delta

    def is_near(self, coordinate: Coordinate, allowed_delta=0.5):
        if not self.position.is_value_known():
            return False

        distance = coordinate.euclidean_distance_from(self.position.get_value())
        return distance < allowed_delta

    def is_near_ball(self, delta=KICKABLE_MARGIN):
        minimum_last_update_time = self.now() - 10
        ball_known = self.world_view.ball.is_value_known(minimum_last_update_time)
        if ball_known:
            return float(self.world_view.ball.get_value().distance) <= delta
        return False

    def is_near_goal(self, delta=10.0):

        if self.world_view.goals[0] is not None and self.world_view.side != self.world_view.goals[0].goal_side:
            return float(self.world_view.goals[0].distance) <= delta

        if self.world_view.goals[1] is not None and self.world_view.side != self.world_view.goals[1].goal_side:
            return float(self.world_view.goals[1].distance) <= delta

        return False

    def now(self):
        return self.world_view.sim_time

    def is_test_player(self):
        return self.num == 7 and self.team_name == "Team2"

    def is_nearest_ball(self, degree=1):
        team_mates = self.world_view.get_teammates(self.team_name, 10)

        if len(team_mates) <= degree:
            return True

        ball_position: Coordinate = self.world_view.ball.get_value().coord
        distances = map(lambda t: t.coord.euclidean_distance_from(ball_position), team_mates)
        sorted_distances = sorted(distances)

        return sorted_distances[degree - 1] > ball_position.euclidean_distance_from(self.position.get_value())

    def ball_interception(self):
        wv = self.world_view
        if wv.ball.is_value_known(self.now() - 4) and wv.ball.get_value().last_position.is_value_known(self.now() - 6):
            if wv.ball_speed() < 0.8:
                return None, None

            project_positions = self.project_ball_position(wv.ball.get_value(), 8)
            for i, position in enumerate(project_positions):
                if self.can_player_reach(position, i + 1):
                    return position, i + 1

        return None, None

    def project_ball_position(self, ball: Ball, ticks: int):
        positions = []

        def advance(previous_location: Coordinate, vx, vy):
            return Coordinate(previous_location.pos_x + vx, previous_location.pos_y + vy)

        if ball.last_position.is_value_known(self.now() - 5) and ball.last_position.last_updated_time <= self.now() - 1:
            last_position = ball.last_position.get_value()
            delta_time = self.world_view.ball.last_updated_time - ball.last_position.last_updated_time
            velocity_x = ((ball.coord.pos_x - last_position.pos_x) / delta_time) * BALL_DECAY
            velocity_y = ((ball.coord.pos_y - last_position.pos_y) / delta_time) * BALL_DECAY
            positions.append(advance(ball.coord, velocity_x, velocity_y))
            offset = self.now() - self.world_view.ball.last_updated_time

            for i in range(1, ticks + offset):
                velocity_x *= BALL_DECAY
                velocity_y *= BALL_DECAY
                positions.append(advance(positions[i - 1], velocity_x, velocity_y))

            return positions[offset:]
        else:
            return []

    def can_player_reach(self, position: Coordinate, ticks):
        run_speed = 1.05 * 0.7  # Account for initial acceleration
        distance = position.euclidean_distance_from(self.position.get_value())
        if self.body_facing(position, delta=20):
            return (ticks - 1) * run_speed >= distance
        else:
            return (ticks - 3) * run_speed >= distance


class ActionHistory:
    def __init__(self) -> None:
        self.turn_heat_map = [0] * 12
        self.last_turn_time = 0
        self.last_orientation_action = 0
        self.last_orientation_time = 0


class BodyState:
    def __init__(self):
        self.time = 0
        self.view_mode = ""
        self.stamina = 0
        self.effort = 0
        self.capacity = 0
        self.speed = 0
        self.direction_of_speed = 0
        self.neck_angle = 0
        self.arm_movable_cycles = 0
        self.arm_expire_cycles = 0
        self.distance = 0
        self.direction = 0
        self.target = ""
        self.tackle_expire_cycles = 0
        self.collision = ""
        self.charged = 0
        self.card = ""


class WorldView:
    def __init__(self, sim_time):
        self.sim_time = sim_time
        self.other_players: [PrecariousData] = []
        self.ball: PrecariousData = PrecariousData.unknown()
        self.goals = []
        self.lines = []
        self.side = ""
        self.game_state = ""

    def __repr__(self) -> str:
        return super().__repr__()

    def ticks_ago(self, ticks):
        return self.sim_time - ticks

    def get_teammates(self, team, max_data_age):
        precarious_filtered = filter(lambda x: (x.is_value_known(self.sim_time - max_data_age)
                                                and x.get_value().team == team), self.other_players)
        return list(map(lambda x: x.get_value(), precarious_filtered))

    def update_player_view(self, observed_player: ObservedPlayer):
        for i, data_point in enumerate(self.other_players):
            p = data_point.get_value()
            if p.num == observed_player.num:
                self.other_players[i].set_value(observed_player, self.sim_time)
                return
        # Add new data point if player does not already exist in list
        self.other_players.append(PrecariousData(observed_player, self.sim_time))

    def ball_speed(self):
        t1 = self.ball.get_value().last_position.last_updated_time
        t2 = self.ball.last_updated_time
        if t1 == t2:
            return 0
        delta_time = t2 - t1
        speed = self.ball.get_value().coord.euclidean_distance_from(self.ball.get_value().last_position.get_value()) / delta_time
        return speed
