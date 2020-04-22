import math

import geometry
from geometry import calculate_full_circle_origin_angle
from player.world_objects import PrecariousData, Coordinate, ObservedPlayer

MAX_MOVE_DISTANCE_PER_TICK = 2.5  # todo random guess. Look up max_speed in manual


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
        self.coach_command = PrecariousData.unknown()
        self.starting_position: Coordinate = None
        self.playing_position: Coordinate = None
        super().__init__()

    def __str__(self) -> str:
        return "side: {0}, team_name: {1}, player_num: {2}, position: {3}".format(self.world_view.side, self.team_name
                                                                                  , self.num, self.position)

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

    def is_near_ball(self, delta=0.6):
        minimum_last_update_time = self.now() - 10
        ball_known = self.world_view.ball.is_value_known(minimum_last_update_time)
        if ball_known:
            return self.is_near(self.world_view.ball.get_value().coord, delta)
        return False

    def now(self):
        return self.world_view.sim_time

    def is_test_player(self):
        return self.num == 2 and self.team_name == "Team1"


class ActionHistory:
    def __init__(self) -> None:
        self.last_turn_time = 0
        self.last_orientation_action = 0


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

