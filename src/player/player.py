import math

import constants
from geometry import calculate_full_origin_angle_radians, is_angle_in_range, smallest_angle_difference, get_xy_vector, \
    Vector2D, inverse_y_axis
from constants import BALL_DECAY, KICKABLE_MARGIN
from player.world_objects import PrecariousData, Coordinate, Ball, ObservedPlayer
from utils import debug_msg

MAX_MOVE_DISTANCE_PER_TICK = 1.05
APPROA_GOAL_DISTANCE = 30

DEFAULT_MODE = "DEFAULT"
INTERCEPT_MODE = "INTERCEPTING"
DRIBBLING_MODE = "DRIBBLING"
CHASE_MODE = "CHASE"
POSSESSION_MODE = "POSSESSION"
PASSED_MODE = "PASSED"
CATCH_MODE = "CATCH"


class PlayerState:

    def __init__(self):
        self.mode = DEFAULT_MODE
        self._ball_seen_since_missing = True
        self.power_rate = constants.DASH_POWER_RATE
        self.team_name = ""
        self.num = -1
        self.player_type = None
        self.ball_collision_time = 0
        self.position: PrecariousData = PrecariousData.unknown()
        self.world_view = WorldView(0)
        self.body_angle: PrecariousData = PrecariousData(0, 0)
        self.action_history = ActionHistory()
        self.body_state = BodyState()
        self.players_close_behind = 0
        self.coach_command = PrecariousData.unknown()
        self.starting_position: Coordinate = None
        self.playing_position: Coordinate = None
        self.last_see_global_angle = 0
        self.current_objective = None
        self.face_dir = PrecariousData(0, 0)
        self.should_reset_to_start_position = False
        self.objective_behaviour = "idle"
        super().__init__()

    def get_y_north_velocity_vector(self):
        return Vector2D.velocity_to_xy(self.body_state.speed, inverse_y_axis(self.body_angle.get_value()))

    def __str__(self) -> str:
        return "side: {0}, team_name: {1}, player_num: {2}, position: {3}".format(self.world_view.side, self.team_name
                                                                                  , self.num, self.position)

    def is_inside_field(self):
        position: Coordinate = self.position.get_value()
        if -52.5 > position.pos_x or position.pos_x > 52.5:
            return False
        if -34 > position.pos_y or position.pos_y > 34:
            return False
        return True


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

        expected_angle = math.degrees(calculate_full_origin_angle_radians(coordinate, self.position.get_value()))
        return abs(smallest_angle_difference(expected_angle, self.body_angle.get_value())) < delta

    def is_near(self, coordinate: Coordinate, allowed_delta=0.5):
        if not self.position.is_value_known():
            return False

        distance = coordinate.euclidean_distance_from(self.position.get_value())
        return distance <= allowed_delta

    def is_near_ball(self, delta=KICKABLE_MARGIN):
        minimum_last_update_time = self.now() - 3
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

    # True if looking towards last known ball position and not seeing the ball
    def is_ball_missing(self):
        if self.world_view.ball.get_value() is None or not self._ball_seen_since_missing:
            # print("ball missing!")
            self._ball_seen_since_missing = False
            return True

        ball_position = self.world_view.ball.get_value().coord
        ball_angle = math.degrees(calculate_full_origin_angle_radians(ball_position, self.position.get_value()))
        angle_difference = abs(self.last_see_global_angle - ball_angle)

        looking_towards_ball = angle_difference < self.body_state.fov * 0.25
        can_see_ball = self.world_view.ball.is_value_known(self.action_history.last_see_update)
        if looking_towards_ball and not can_see_ball:
            pass
            # print("ball missing!")

        return looking_towards_ball and not can_see_ball

    def now(self):
        return self.world_view.sim_time

    def is_test_player(self):
        return self.num == 2 and self.team_name == "Team1"

    def is_nearest_ball(self, degree=1):
        team_mates = self.world_view.get_teammates(self.team_name, 10)

        if len(team_mates) < degree:
            return True

        ball_position: Coordinate = self.world_view.ball.get_value().coord
        distances = map(lambda t: t.coord.euclidean_distance_from(ball_position), team_mates)
        sorted_distances = sorted(distances)

        return sorted_distances[degree - 1] > ball_position.euclidean_distance_from(self.position.get_value())

    def ball_interception(self):
        wv = self.world_view
        ball = wv.ball.get_value()
        ball_known = wv.ball.is_value_known(self.now() - 4)
        if (not ball_known) or ball.absolute_velocity is None or ball.absolute_velocity.magnitude() < 0.2:
            return None, None

        if wv.ball.is_value_known(self.now() - 4):
            ball: Ball = wv.ball.get_value()

            tick_offset = self.now() - wv.ball.last_updated_time
            project_positions = ball.project_ball_position(10, tick_offset)
            if project_positions is None:
                return None, None

            all_ticks = range(1, 11)
            positions_and_ticks = zip(project_positions, all_ticks)
            printable_list = [(pt[0], pt[1]) for pt in positions_and_ticks]
            #positions_and_ticks = sorted(positions_and_ticks, key=lambda pos_and_t: pos_and_t[0].euclidean_distance_from(self.position.get_value()))

            for (position, tick) in positions_and_ticks:
                if self.can_player_reach(position, tick):
                    debug_msg(str(self.now()) + " | Based on ball velocity : " + str(ball.absolute_velocity)
                              , "INTERCEPTION")
                    debug_msg(str(self.now()) + " | Projected (coord, tick_offset): "
                              + str(printable_list), "INTERCEPTION")
                    return position, tick

            if self.is_test_player():
                debug_msg(str(self.now()) + " | Based on ball velocity : " + str(ball.absolute_velocity)
                          , "INTERCEPTION")
                debug_msg(str(self.now()) + " | Predictions : " + str(printable_list)
                          , "INTERCEPTION")

        return None, None

    def can_player_reach(self, position: Coordinate, ticks):
        distance = position.euclidean_distance_from(self.position.get_value())
        extra_time = 1

        if distance <= KICKABLE_MARGIN:
            return True

        if not self.body_facing(position, delta=5):
            extra_time += 1
            if self.body_state.speed > 0.2:
                extra_time += 1

        return self.time_to_rush_distance(distance) <= ticks + extra_time


    def time_to_rush_distance(self, distance):
        def distance_in_n_ticks(speed, ticks):
            if ticks == 0:
                return 0
            return speed + distance_in_n_ticks(speed * constants.PLAYER_SPEED_DECAY, ticks - 1)

        projected_speed = 0
        ticks = 0
        while distance > distance_in_n_ticks(projected_speed, 3):
            ticks += 1
            projected_speed += constants.DASH_POWER_RATE * 100
            distance -= projected_speed
            projected_speed *= constants.PLAYER_SPEED_DECAY
        return ticks + 3

    def update_body_angle(self, new_angle, time):
        # If value is uninitialized, then accept new_angle as actual angle
        self.body_angle.set_value(new_angle, time)

    def update_position(self, new_position: Coordinate):
        self.position.set_value(new_position, self.now())
        # print("PARSED : ", time, " | Position: ", new_position)
        self.action_history.projected_position = new_position

    def update_face_dir(self, new_global_angle):
        if self.action_history.turn_in_progress:
            history = self.action_history
            actual_angle_change = abs(new_global_angle - self.face_dir.get_value())

            if history.missed_turn_last_see:
                # Missed turn update in last see message, so it must have been included in this see update
                history.turn_in_progress = False
                history.missed_turn_last_see = False
                history.expected_body_angle = None
            elif actual_angle_change + 0.1 >= abs(history.expected_angle_change) / 2 or actual_angle_change > 2.0:
                # Turn registered
                history.turn_in_progress = False
                history.expected_body_angle = None
            else:
                # Turn not registered
                history.missed_turn_last_see = True

            # Reset expected angle
            history.expected_angle_change = 0

        self.last_see_global_angle = new_global_angle
        self.face_dir.set_value(new_global_angle, self.now())
        self.update_body_angle(new_global_angle - self.body_state.neck_angle, self.now())

    def on_see_update(self):
        self.action_history.three_see_updates_ago = self.action_history.two_see_updates_ago
        self.action_history.two_see_updates_ago = self.action_history.last_see_update
        self.action_history.last_see_update = self.now()

        if self.current_objective is not None:
            self.current_objective.has_processed_see_update = False

        if self.world_view.ball.last_updated_time == self.action_history.last_see_update:
            # We've seen the ball this tick, so it is not missing
            self._ball_seen_since_missing = True
        elif self.is_ball_missing():
            # We're looking in the direction of the ball and not seeing it, so it must be missing
            self._ball_seen_since_missing = False

    def update_ball(self, new_ball: Ball, time):
        self.world_view.ball.set_value(new_ball, time)
        self._ball_seen_since_missing = True

    def ball_incoming(self):
        if not self.world_view.ball.is_value_known(self.action_history.three_see_updates_ago):
            return False

        ball: Ball = self.world_view.ball.get_value()
        dist = ball.distance
        if ball.absolute_velocity is not None:
            ball_move_dir = ball.absolute_velocity.world_direction()
            ball_relative_dir = self.face_dir.get_value() + ball.direction
            dif = abs(smallest_angle_difference((ball_move_dir + 180) % 360, ball_relative_dir))
            return dif < 15

        position, projected_direction, speed = ball.approximate_position_direction_speed(2)
        if projected_direction is None or speed < 0.25:
            return False

        ball_angle = math.degrees(calculate_full_origin_angle_radians(self.position.get_value(), ball.coord))
        if abs(ball_angle - projected_direction) < 15 and dist < 40:
            return True

        return False

    def is_inside_own_box(self) -> bool:
        pos: Coordinate = self.position.get_value()

        result = True
        if self.world_view.side == "l":
            if pos.pos_x > -36 or (pos.pos_y < -20 or pos.pos_y > 20):
                result = False
        else:
            if pos.pos_x < 36 or (pos.pos_y < -20 or pos.pos_y > 20):
                result = False

        if self.is_test_player():
            debug_msg("is_inside_own_box={0}, Pos={1}".format(result, pos), "GOALIE")

        return result


class ActionHistory:
    def __init__(self) -> None:
        self.turn_history = ViewFrequency()
        self.ball_focus_actions = 0
        self.last_see_update = 0
        self.last_catch = 0
        self.two_see_updates_ago = 0
        self.three_see_updates_ago = 0
        self.has_just_intercept_kicked = False
        self.turn_in_progress = False
        self.missed_turn_last_see = False
        self.expected_speed = None
        self.projected_position = Coordinate(0, 0)
        self.has_looked_for_targets = False
        self.expected_angle_change = 0
        self.expected_body_angle = None
        self.last_look_for_pass_targets = 0


class ViewFrequency:
    SLICE_WIDTH = 15  # The amount of degrees between each view 'slice'
    SLICES = round(360 / SLICE_WIDTH)

    def __init__(self) -> None:
        self.last_update_time: [int] = [0] * self.SLICES

    def least_updated_angle(self, field_of_view, lower_bound=0, upper_bound=360):
        viewable_slices_to_each_side = self._get_viewable_slices_to_each_side(field_of_view)

        oldest_angle = 0
        best_angle_index = 0

        for i, update_time in enumerate(self.last_update_time):
            if not is_angle_in_range(i * self.SLICE_WIDTH, lower_bound, upper_bound):
                continue

            viewable_range = range(i - viewable_slices_to_each_side, i + viewable_slices_to_each_side + 1)
            total_age = 0
            for v in viewable_range:
                total_age += self.last_update_time[v % self.SLICES]

            if oldest_angle < total_age:
                oldest_angle = total_age
                best_angle_index = i

        return self.SLICE_WIDTH * best_angle_index

    def renew_angle(self, angle: int, field_of_view: int):
        viewable_slices_to_each_side = self._get_viewable_slices_to_each_side(field_of_view)
        angle_index = round(angle / self.SLICE_WIDTH)
        view_range = range(angle_index - viewable_slices_to_each_side, angle_index + viewable_slices_to_each_side + 1)

        # Increment all timers
        for i in range(0, len(self.last_update_time)):
            self.last_update_time[i] = min(self.last_update_time[i] + 1, 20)

        # Reset now visible angles
        for i in view_range:
            self.last_update_time[i % self.SLICES] = 0

    def _get_viewable_slices_to_each_side(self, field_of_view) -> int:
        viewable_slices = math.floor(field_of_view / self.SLICE_WIDTH)
        if viewable_slices % 2 == 0:
            viewable_slices -= 1
        return max(math.floor(viewable_slices / 2), 0)


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
        self.fov = 90


class WorldView:
    def __init__(self, sim_time):
        self.sim_time = sim_time
        self.other_players: [PrecariousData] = []
        self.ball: PrecariousData = PrecariousData.unknown()
        self.goals = []
        self.lines = []
        self.side = ""
        self.game_state = "before_kick_off"

    def __repr__(self) -> str:
        return super().__repr__()

    def is_marked(self, team, max_data_age, min_distance=3):
        opponents: [ObservedPlayer] = self.get_teammates(team, max_data_age=max_data_age)
        for opponent in opponents:
            if opponent.distance < min_distance:
                return True

        return False

    def ticks_ago(self, ticks):
        return self.sim_time - ticks

    def team_has_ball(self, team, max_data_age, min_possession_distance=3):
        if not self.ball.is_value_known():
            debug_msg("{0} has ball".format("Team2"), "HAS_BALL")
            return False

        all_players: [ObservedPlayer] = self.get_all_known_players(team, max_data_age)

        # Sort players by distance to ball
        sorted_list: [ObservedPlayer] = list(sorted(all_players, key=lambda p: p.coord.euclidean_distance_from(self.ball.get_value().coord), reverse=False))

        if len(sorted_list) < 1:
            return False

        # If closest player to ball team is known and is our team, return True
        closest_player: ObservedPlayer = sorted_list[0]
        if closest_player.team is not None and closest_player.team == team and closest_player.coord.euclidean_distance_from(self.ball.get_value().coord) < min_possession_distance:
            debug_msg("{0} has ball | player: {1}".format(team, closest_player), "HAS_BALL")
            return True

        debug_msg("{0} has ball".format("Team2"), "HAS_BALL")
        return False


    def get_all_known_players(self, team, max_data_age):
        all_players: [ObservedPlayer] = []
        all_players.extend(self.get_teammates(team, max_data_age))
        all_players.extend(self.get_opponents(team, max_data_age))
        return all_players

    def get_free_forward_team_mates(self, team, side, my_coord: Coordinate, max_data_age, min_distance_free, min_dist_from_me=3):
        free_team_mates: [ObservedPlayer] = self.get_free_team_mates(team, max_data_age, min_distance_free)
        if side == "l":
            free_forward_team_mates = list(filter(lambda p: p.coord.pos_x > my_coord.pos_x and p.coord.euclidean_distance_from(my_coord) > min_dist_from_me, free_team_mates))
        else:
            free_forward_team_mates = list(filter(lambda p: p.coord.pos_x < my_coord.pos_x and p.coord.euclidean_distance_from(my_coord) > min_dist_from_me, free_team_mates))

        return free_forward_team_mates

    def get_non_offside_forward_team_mates(self, team, side, my_coord: Coordinate, max_data_age, min_distance_free, min_dist_from_me=1):
        free_forward_team_mates: [ObservedPlayer] = self.get_free_forward_team_mates(team, side, my_coord, max_data_age, min_distance_free, min_dist_from_me)
        opponents: [ObservedPlayer] = self.get_opponents(team, max_data_age)

        # If no opponents are seen, no one is offside
        if len(opponents) < 1:
            return free_forward_team_mates

        reverse = True if side == "l" else False
        furthest_behind_opponent: ObservedPlayer = list(sorted(opponents, key=lambda p: p.coord.pos_x, reverse=reverse))[0]
        furthest_opp_x_pos = furthest_behind_opponent.coord.pos_x
        if side == "l":
            non_offside_players = list(filter(lambda p: (p.coord.pos_x < furthest_opp_x_pos
                                                        and p.coord.euclidean_distance_from(my_coord) > min_dist_from_me)
                                                        or p.coord.pos_x < 0, free_forward_team_mates))
        else:
            non_offside_players = list(filter(lambda p: (p.coord.pos_x > furthest_opp_x_pos
                                                        and p.coord.euclidean_distance_from(my_coord) > min_dist_from_me)
                                                        or p.coord.pos_x > 0, free_forward_team_mates))
        debug_msg("Further_opp_x_pos={0} | free_forward_team_mates={1} | furthest_behind_opponent={2} | non_offisde_players={3}".format(furthest_opp_x_pos, free_forward_team_mates, furthest_behind_opponent, non_offside_players), "OFFSIDE")
        return non_offside_players

    def get_free_behind_team_mates(self, team, side, my_coord: Coordinate, max_data_age, min_distance_free, min_dist_from_me=3):
        free_team_mates: [ObservedPlayer] = self.get_free_team_mates(team, max_data_age, min_distance_free)
        if side == "l":
            free_behind_team_mates = list(filter(lambda p: p.coord.pos_x < my_coord.pos_x
                                                           and p.coord.euclidean_distance_from(my_coord) > min_dist_from_me
                                                           and p.num != 1, free_team_mates))
        else:
            free_behind_team_mates = list(filter(lambda p: p.coord.pos_x > my_coord.pos_x and p.coord.euclidean_distance_from(my_coord) > min_dist_from_me, free_team_mates))

        return free_behind_team_mates

    def get_teammates(self, team, max_data_age):
        precarious_filtered = filter(lambda x: (x.is_value_known(self.sim_time - max_data_age)
                                                and x.get_value().team == team), self.other_players)
        return list(map(lambda x: x.get_value(), precarious_filtered))

    def get_opponents(self, team, max_data_age):
        precarious_filtered = filter(lambda x: (x.is_value_known(self.sim_time - max_data_age)
                                                and x.get_value().team != team), self.other_players)
        return list(map(lambda x: x.get_value(), precarious_filtered))

    def get_free_team_mates(self, team, max_data_age, min_distance=2) -> [ObservedPlayer]:
        team_mates: [ObservedPlayer] = self.get_teammates(team, max_data_age=max_data_age)
        opponents: [ObservedPlayer] = self.get_opponents(team, max_data_age=max_data_age)

        debug_msg("Team_mates={0} | opponents={1} | other_players:{2}".format(team_mates, opponents, self.other_players), "OFFSIDE")

        free_team_mates = []

        for team_mate in team_mates:
            for opponent in opponents:
                tm: ObservedPlayer = team_mate
                op: ObservedPlayer = opponent
                if tm.coord.euclidean_distance_from(op.coord) > min_distance and tm not in free_team_mates:
                    free_team_mates.append(tm)

        return free_team_mates

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
        distance = self.ball.get_value().coord.euclidean_distance_from(self.ball.get_value().last_position.get_value())
        speed = distance / delta_time
        return speed
