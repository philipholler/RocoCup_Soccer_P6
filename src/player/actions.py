import math
from logging import debug
from random import choice

from sympy import solve, Eq, Symbol

import geometry
from constants import PLAYER_JOG_POWER, PLAYER_RUN_POWER, KICK_POWER_RATE, BALL_DECAY, \
    KICKABLE_MARGIN, FOV_NARROW, FOV_NORMAL, FOV_WIDE, PLAYER_SPEED_DECAY, PLAYER_MAX_SPEED, DASH_POWER_RATE
from geometry import calculate_full_origin_angle_radians, is_angle_in_range, smallest_angle_difference

from player.player import PlayerState
from player.world_objects import Coordinate, ObservedPlayer, Ball, PrecariousData

ORIENTATION_ACTIONS = ["(turn_neck 90)", "(turn_neck -180)", "(turn 180)", "(turn_neck 90)"]
NECK_ORIENTATION_ACTIONS = ["(turn_neck 90)", "(turn_neck -180)"]

IDLE_ORIENTATION_INTERVAL = 50
POSSESSION_ORIENTATION_INTERVAL = 2

SET_VIEW_NORMAL = "(change_view normal high)"
SET_VIEW_NARROW = "(change_view narrow high)"
SET_VIEW_WIDE = "(change_view wide high)"

MAX_TICKS_PER_SEE_UPDATE = 4  # todo Correct?


class Command:
    def __init__(self, messages: [str] = None, urgent=False, on_execute=lambda: None) -> None:
        if messages is None:
            self.messages = []
        else:
            self.messages = messages
        self.urgent = urgent
        self._attached_functions = [on_execute]

    def append_action(self, action: str):
        self.messages.append(action)

    def add_function(self, f):
        self._attached_functions.append(f)

    def __repr__(self) -> str:
        return str(self.messages) + ", urgent: " + str(self.urgent)

    def execute_attached_functions(self):
        for f in self._attached_functions:
            f()


class CommandBuilder:
    def __init__(self) -> None:
        self.command_list: [Command] = [Command()]
        self.ticks = 0

    def append_action(self, action, urgent=False):
        cmd = self.command_list[self.ticks]
        cmd.append_action(action)
        if urgent:
            cmd.urgent = True

    def append_turn_action(self, state: PlayerState, turn_moment, urgent=False):
        self.append_action("(turn {0})".format(turn_moment), urgent)
        self._current_command().add_function(lambda: project_body_angle(state, turn_moment))

    def append_dash_action(self, state, power, urgent=False):
        self.append_action("(dash {0})".format(power), urgent)
        # self.command_list[self.ticks].add_function(lambda: project_speed(state, power))

    def next_tick(self):
        self.ticks += 1
        self.command_list.append(Command())

    def _current_command(self):
        return self.command_list[self.ticks]


def project_body_angle(state: PlayerState, turn_moment):
    current_angle = state.body_angle.get_value()
    turn_angle = calculate_actual_turn_angle(state, turn_moment)
    state.action_history.expected_angle = current_angle + turn_angle
    print(state.now() + 1, " Projecting angle. Old angle: ", current_angle, " | new angle: ", current_angle + turn_angle)


def project_dash(state, dash_power):
    state.body_state.speed = calculate_actual_speed(state.body_state.speed, dash_power)
    # todo: project position too?


def orient_if_position_or_angle_unknown(function):
    def wrapper(*args, **kwargs):
        state: PlayerState = args[0]
        time_limit = state.action_history.last_see_update
        if (not state.position.is_value_known(time_limit)) or not state.body_angle.is_value_known(time_limit):
            print("Oriented instead of : " + str(function) + " because position or angle is unknown")
            return [Command(_orient(state, neck_movement_only=True))]
        else:
            return function(*args, **kwargs)

    return wrapper


@orient_if_position_or_angle_unknown
def plan_rush_to(state: PlayerState, target: Coordinate):
    commandBuilder = CommandBuilder()

    dist = target.euclidean_distance_from(state.position.get_value())
    print("time : ", state.action_history.last_see_update, " | angle to target: ",
          calculate_relative_angle(state, target), " | dist: ", dist)
    if dist <= 1.0:
        # Dash last distance
        target_speed = dist
        power, projected_speed = calculate_power(state.body_state.speed, target_speed)
        commandBuilder.append_dash_action(state, power, urgent=True)
        commandBuilder.next_tick()

        # Brake to speed 0
        dist -= projected_speed
        projected_speed *= PLAYER_SPEED_DECAY
        power, projected_speed = calculate_power(projected_speed, 0)
        commandBuilder.append_dash_action(state, power, urgent=True)

        return commandBuilder.command_list

    if not state.body_facing(target, 3):
        rotation = calculate_relative_angle(state, target)
        turn_moment = round(calculate_turn_moment(state, rotation), 2)

        if turn_moment < 0:
            first_turn_moment = max(turn_moment, -180)
        else:
            first_turn_moment = min(turn_moment, 180)
        commandBuilder.append_turn_action(state, first_turn_moment)
        commandBuilder.next_tick()

        # state.body_angle.get_value()
        print(commandBuilder.command_list)
        # | Commands : ", commands)

        # if necessary to turn again:
        second_turn_moment = turn_moment - first_turn_moment
        if abs(second_turn_moment) > 0.5:  # If turn could not be completed in one tick, perform it after
            print("one turn not enough!")
            commandBuilder.append_turn_action(state, second_turn_moment)
            commandBuilder.next_tick()

    # Might need to account for direction after turning
    projected_speed = state.body_state.speed
    projected_dist = dist
    for i in range(0,
                   commandBuilder.ticks):  # Account for position and speed after possible spending some ticks turning
        projected_dist -= projected_speed
        projected_speed *= PLAYER_SPEED_DECAY

    # Add dash commands for remaining amount of ticks
    for i in range(commandBuilder.ticks, MAX_TICKS_PER_SEE_UPDATE):
        target_speed = min(projected_dist, PLAYER_MAX_SPEED)
        power, projected_speed = calculate_power(projected_speed, target_speed)
        commandBuilder.append_dash_action(state, power)
        commandBuilder.next_tick()

        # Predict new dist to target and speed
        projected_dist -= projected_speed
        projected_speed *= PLAYER_SPEED_DECAY  # todo should this be urgent if power is negative? (ie. braking)

    return commandBuilder.command_list


def reset_neck(state):
    return ["(turn_neck " + str(-state.body_state.neck_angle) + ")"]


def dribble_towards(state: PlayerState, target_position: Coordinate):
    minimum_last_update_time = state.now() - 3
    angle_known = state.body_angle.is_value_known(minimum_last_update_time)
    position_known = state.position.is_value_known(minimum_last_update_time)

    if not angle_known or not position_known:
        return idle_neck_orientation(state)

    if state.is_near_ball(KICKABLE_MARGIN):
        direction = calculate_relative_angle(state, target_position)
        actions: [] = ["(kick {0} {1})".format("20", direction), "(dash 70)"]
        return actions
    else:
        return run_towards_ball(state)


def jog_towards(state: PlayerState, target_position: Coordinate, speed=PLAYER_JOG_POWER):
    actions = [SET_VIEW_NARROW]
    history = state.action_history
    minimum_last_update_time = state.now() - 3
    angle_known = state.body_angle.is_value_known(minimum_last_update_time)
    position_known = state.position.is_value_known(minimum_last_update_time)

    dist = -state.position.get_value().pos_x
    print(str(dist))
    if dist > 0:
        if state.action_history.should_break:
            return ["(dash -80)"]
        else:
            state.action_history.last_dash_time = state.now()
            if dist < 2.5:
                state.action_history.should_break = True
            return [SET_VIEW_NARROW, "(dash 100)"]
    else:
        return []

    if not angle_known or not position_known:
        return idle_orientation(state)

    distance = target_position.euclidean_distance_from(state.position.get_value())
    if distance < 0.6:
        return look_at_ball(state)

    if not state.action_history.has_turned_since_last_see and not state.body_facing(target_position, 5):
        rotation = calculate_relative_angle(state, target_position)
        print(rotation)
        history.last_turn_time = state.now()
        actions.append("(turn " + str(calculate_turn_moment(state, rotation)) + ")")
    else:
        if distance > 3 or state.action_history.last_dash_time < state.action_history.last_see_update:
            distance = state.position.get_value().euclidean_distance_from(target_position)
            actions.append("(dash {0})".format(str(calculate_dash_power(state, distance, speed))))
            state.action_history.last_dash_time = state.now()

    actions.extend(idle_neck_orientation(state))
    return actions


def calculate_dash_power(state: PlayerState, distance, speed):
    if distance < 3:
        if (state.speed) > distance:
            return -10
        return 25 + distance * 5
    return speed


def run_towards_ball(state: PlayerState):
    minimum_last_update_time = state.now() - 5
    ball_known = state.world_view.ball.is_value_known(minimum_last_update_time)

    if not ball_known:
        return locate_ball(state)

    if state.world_view.ball.get_value().distance < 2.5:
        pass  # todo

    return jog_towards(state, state.world_view.ball.get_value().coord, PLAYER_RUN_POWER)


def choose_rand_player(player_passing: PlayerState):
    team_mates = player_passing.world_view.get_teammates(player_passing.team_name, 10)
    if len(team_mates) != 0:
        return choice(team_mates)
    return None


def pass_ball_to(target: ObservedPlayer, state: PlayerState):
    world = state.world_view

    if world.ball.is_value_known(world.ticks_ago(5)) and state.position.is_value_known(world.ticks_ago(5)):
        ball = world.ball.get_value()
        if state.is_near_ball(KICKABLE_MARGIN):
            if target is not None:
                print("Kicking from player {0} to player {1}".format(str(state.num), str(target.num)))
                direction = calculate_relative_angle(state, target.coord)
                distance = state.position.get_value().euclidean_distance_from(target.coord)
                return ["(kick " + str(calculate_kick_power(state, distance) * 0.8) + " " + str(direction) + ")"]
            else:
                return idle_neck_orientation(state)
        else:
            return run_towards_ball(state)
    else:
        return idle_neck_orientation(state)


def pass_ball_to_random(state: PlayerState):
    target: ObservedPlayer = choose_rand_player(state)
    if target is None:
        return idle_neck_orientation(state)

    direction = calculate_relative_angle(state, target.coord)
    power = calculate_kick_power(state, target.distance)

    return ["(kick " + str(power) + " " + str(direction) + ")"]


def kick_to_goal(player: PlayerState):
    if player.team_name == "Team1":
        target = Coordinate(53.0, 0)
    else:
        target = Coordinate(-53.0, 0)

    direction = calculate_relative_angle(player, target)

    return ["(kick " + str(160) + " " + str(direction) + ")"]


def require_see_update(function):
    def wrapper(*args, **kwargs):
        if args[0].action_history.has_turned_since_last_see:
            return []
        else:
            return function(*args, **kwargs)

    return wrapper


# Can turn both neck and body to look at the ball
@require_see_update
def look_at_ball(state: PlayerState):
    if not state.body_angle.is_value_known(state.action_history.last_see_update):
        return locate_ball(state)

    fov_command, fov_size = determine_fov(state)
    actions = [fov_command]

    ball_coord = state.world_view.ball.get_value().coord
    ball_direction = math.degrees(calculate_full_origin_angle_radians(ball_coord, state.position.get_value()))
    actions.extend(look_direction(state, ball_direction, fov_size))
    return actions


@require_see_update
def locate_ball(state: PlayerState):
    actions = [SET_VIEW_WIDE]
    if not state.body_angle.is_value_known(state.now() - 10):
        print("angle unknown")
        return actions

    turn_history = state.action_history.turn_history
    angle = turn_history.least_updated_angle(FOV_WIDE)
    actions.extend(look_direction(state, angle, FOV_WIDE))
    state.action_history.has_turned_since_last_see = True
    return actions


# Creates turn commands (both neck and body)
# to face the total angle of the player in the target direction
@require_see_update
def look_direction(state: PlayerState, target_direction, fov):
    actions = []
    current_total_direction = state.body_angle.get_value() + state.body_state.neck_angle

    body_angle = state.body_angle.get_value()
    # Case where it is enough to turn neck
    if is_angle_in_range(target_direction, from_angle=(body_angle - 90) % 360, to_angle=(body_angle + 90) % 360):
        angle_to_turn = round(smallest_angle_difference(target_direction, current_total_direction), 2)
        actions.append("(turn_neck {0})".format(angle_to_turn))
    # Case where it is necessary to turn body
    else:
        angle_to_turn_body = smallest_angle_difference(target_direction, state.body_angle.get_value())
        actions.extend(reset_neck(state))
        actions.append("(turn {0})".format(round(angle_to_turn_body), 2))

    # Update state to show that this angle has now been viewed
    state.action_history.turn_history.renew_angle(target_direction, fov)
    state.action_history.has_turned_since_last_see = True
    return actions


@require_see_update
def idle_neck_orientation(state: PlayerState):
    return idle_orientation(state, neck_movement_only=True)


@require_see_update
def idle_orientation(state, neck_movement_only=False):
    # Perform an orientation with boundaries of neck movement
    state.action_history.last_orientation_action = 0
    return [Command(_orient(state, neck_movement_only))]


@require_see_update
def look_for_pass_target(state: PlayerState):
    # Perform an orientation with boundaries of neck movement
    if state.action_history.last_orientation_action >= POSSESSION_ORIENTATION_INTERVAL:
        state.action_history.last_orientation_action = 0
        return _orient(state, False)
    else:
        state.action_history.last_orientation_action += 1
        return look_at_ball(state)


def _orient(state, neck_movement_only):
    fov_command, fov_size = determine_fov(state)
    immediate_actions = [fov_command]
    turn_history = state.action_history.turn_history

    body_angle = state.body_angle.get_value()
    if neck_movement_only:  # Limit movement to within neck range
        lower_bound = (body_angle - 90) % 360
        upper_bound = (body_angle + 90) % 360
    else:  # Allow any turn movement (both body and neck)
        lower_bound = 0
        upper_bound = 360

    angle = turn_history.least_updated_angle(FOV_WIDE, lower_bound, upper_bound)
    immediate_actions.extend(look_direction(state, angle, FOV_WIDE))
    state.action_history.has_turned_since_last_see = True

    state.action_history.last_orientation_action = 0
    return immediate_actions


def determine_fov(state: PlayerState):
    if state.world_view.ball.is_value_known(state.now() - 6) and state.position.is_value_known(state.now() - 6):
        dist_to_ball = state.world_view.ball.get_value().coord.euclidean_distance_from(state.position.get_value())

        if dist_to_ball < 15:
            return SET_VIEW_NARROW, FOV_NARROW
        elif dist_to_ball < 25:
            return SET_VIEW_NORMAL, FOV_NORMAL
        else:
            return SET_VIEW_WIDE, FOV_WIDE

    return SET_VIEW_WIDE, FOV_WIDE


def calculate_relative_angle(player_state, target_position):
    rotation = calculate_full_origin_angle_radians(target_position, player_state.position.get_value())
    rotation = math.degrees(rotation)
    rotation -= player_state.body_angle.get_value()

    # Pick the short way around (<180 degrees)
    if rotation > 180:
        rotation -= 360
    elif rotation < -180:
        rotation += 360

    return rotation


def _calculate_ball_velocity_vector(state: PlayerState):
    if state.world_view.ball.is_value_known():
        ball: Ball = state.world_view.ball.get_value()
        last_position = ball.last_position.get_value()
        delta_time = state.world_view.ball.last_updated_time - ball.last_position.last_updated_time
        velocity_x = ((ball.coord.pos_x - last_position.pos_x) / delta_time) * BALL_DECAY
        velocity_y = ((ball.coord.pos_y - last_position.pos_y) / delta_time) * BALL_DECAY
        return velocity_x, velocity_y


def stop_ball(state: PlayerState):
    if state.world_view.ball.is_value_known(state.now() - 1) and state.body_angle.is_value_known(state.now() - 1):
        ball: Ball = state.world_view.ball.get_value()

        velocity_vector_x, velocity_vector_y = _calculate_ball_velocity_vector(state)

        # Calculate ball direction from origin
        ball_global_dir = math.degrees(
            calculate_full_origin_angle_radians(Coordinate(velocity_vector_x, velocity_vector_y), Coordinate(0, 0)))

        # Kick angle should be opposite of ball direction
        global_kick_angle = (ball_global_dir - 180) % 360
        # x = kickpower (0-100)
        kick_difference = Symbol('kick_difference', real=True)
        eq = Eq(state.body_angle.get_value() + kick_difference, global_kick_angle)
        relative_kick_angle = solve(eq)[0]

        # Get ball speed needed to calculate power of stopping kick
        ball_speed = state.world_view.ball_speed()

        # Find kick power depending on ball direction from player, ball distance from player, ball speed decay, kickable margin as well as ball speed
        # x = kickpower (0-100)
        x = Symbol('x', real=True)
        eqn = Eq(((x * KICK_POWER_RATE) * (
                    1 - 0.25 * (abs(ball.direction) / 180) - 0.25 * (ball.distance / KICKABLE_MARGIN)) * BALL_DECAY),
                 ball_speed)
        kick_power = solve(eqn)[0]

        '''
        print("Vel_vec: ", velocity_vector)
        print("Ball_global_dir: ", ball_global_dir)
        print("kick_angle", relative_kick_angle)
        print("ball_speed", ball_speed)
        print("kick_power", kick_power)
        '''
        print("Stopping ball... kick_power={0}, kick_angle={1}, ball_speed={2}".format(kick_power, relative_kick_angle,
                                                                                       ball_speed))
        return ["(kick {0} {1})".format(kick_power, relative_kick_angle)]

    return []


def calculate_kick_power(state: PlayerState, distance: float) -> int:
    ball: Ball = state.world_view.ball.get_value()
    dir_diff = abs(ball.direction)
    dist_ball = ball.distance

    # voodoo parameters
    if distance > 40:
        time_to_target = int(distance * 1.4)
    elif distance >= 30:
        time_to_target = int(distance * 1.35)
    elif distance >= 20:
        time_to_target = int(distance * 1.25)
    elif distance >= 10:
        time_to_target = int(distance * 1.15)
    else:
        time_to_target = 3

    # Solve for the initial kick power needed to get to the distance after time_to_target ticks
    # x = kickpower (0-100)
    x = Symbol('x', real=True)
    eqn = Eq(sum([(((x * KICK_POWER_RATE) * (1 - 0.25 * (dir_diff / 180) - 0.25 * (dist_ball / KICKABLE_MARGIN)))
                   * BALL_DECAY ** i) for i in range(0, time_to_target)]), distance)
    solution = solve(eqn)
    if len(solution) == 0:
        print(solution)
        print("Time_to_target: {0}, dist_ball: {1}, dir_diff: {2}, player: {3}".format(time_to_target, dist_ball,
                                                                                       dir_diff, state))
    needed_kick_power = solve(eqn)[0]

    if needed_kick_power < 0:
        raise Exception("Should not be able to be negative. What the hell - Philip")
    elif needed_kick_power > 100:
        pass
        # print("Tried to kick with higher than 100 power: ", str(needed_kick_power), ", player: ", state)

    return needed_kick_power


def calculate_turn_moment(state: PlayerState, target_angle):
    return target_angle * (1 + 5 * state.body_state.speed)


def calculate_actual_turn_angle(state: PlayerState, moment):
    return moment / (1 + 5 * state.body_state.speed)


def calculate_power(current_speed, target_speed):
    delta = target_speed - current_speed
    power = delta / DASH_POWER_RATE

    if power < 0:
        power = max(power, -100)
    else:
        power = min(power, 100)

    projected_speed = current_speed + power * DASH_POWER_RATE
    return power, projected_speed


def calculate_actual_speed(current_speed, dash_power):
    return current_speed + dash_power * DASH_POWER_RATE
