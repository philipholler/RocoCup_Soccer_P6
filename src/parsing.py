import math
import re

from coaches.world_objects_coach import WorldViewCoach, PlayerViewCoach, BallOnlineCoach
from geometry import calculate_smallest_origin_angle_between, rotate_coordinate, get_object_position, \
    calculate_full_origin_angle_radians, smallest_angle_difference, find_mean_angle
from player import player, world_objects
from math import sqrt

from player.player import PlayerState
from player.world_objects import Coordinate, Ball
from player.world_objects import ObservedPlayer
from player.world_objects import PrecariousData
from utils import debug_msg

_REAL_NUM_REGEX = "[-0-9]*\\.?[0-9]*"
_SIGNED_INT_REGEX = "[-0-9]+"
_ROBOCUP_MSG_REGEX = "[-0-9a-zA-Z ().+*/?<>_]*"
_SEE_MSG_REGEX = "\\(\\([^\\)]*\\)[^\\)]*\\)"
_TEAM_NAME_REGEX = "(−|_|a-z|A−Z|0−9)+"

# Introduced to reduce calculation time
MAX_FLAGS_FOR_POSITION_ESTIMATE = 10

_FLAG_COORDS = {
    # perimiter flags
    "tl50": (-50, 39),
    "tl40": (-40, 39),
    "tl30": (-30, 39),
    "tl20": (-20, 39),
    "tl10": (-10, 39),
    "t0": (0, 39),
    "tr10": (10, 39),
    "tr20": (20, 39),
    "tr30": (30, 39),
    "tr40": (40, 39),
    "tr50": (50, 39),

    "rt30": (57.5, 30),
    "rt20": (57.5, 20),
    "rt10": (57.5, 10),
    "r0": (57.5, 0),
    "rb10": (57.5, -10),
    "rb20": (57.5, -20),
    "rb30": (57.5, -30),

    "bl50": (-50, -39),
    "bl40": (-40, -39),
    "bl30": (-30, -39),
    "bl20": (-20, -39),
    "bl10": (-10, -39),
    "b0": (0, -39),
    "br10": (10, -39),
    "br20": (20, -39),
    "br30": (30, -39),
    "br40": (40, -39),
    "br50": (50, -39),

    "lt30": (-57.5, 30),
    "lt20": (-57.5, 20),
    "lt10": (-57.5, 10),
    "l0": (-57.5, 0),
    "lb10": (-57.5, -10),
    "lb20": (-57.5, -20),
    "lb30": (-57.5, -30),

    # goal flags ('t' and 'b' flags can change based on server parameter
    # 'goal_width', but we leave their coords as the default values.
    "glt": (-52.5, 7.0),
    "gl": (-52.5, 0),
    "glb": (-52.5, -7.0),

    "grt": (52.5, 7.0),
    "gr": (52.5, 0),
    "grb": (52.5, -7.0),

    # penalty flags
    "plt": (-36, 20),
    "plc": (-36, 0),
    "plb": (-36, -20),

    "prt": (36, 20),
    "prc": (36, 0),
    "prb": (36, -20),

    # field boundary flags (on boundary lines)
    "lt": (-52.5, 34),
    "ct": (0, 34),
    "rt": (52.5, 34),

    "lb": (-52.5, -34),
    "cb": (0, -34),
    "rb": (52.5, -34),

    # center flag
    "c": (0, 0)
}


def parse_pass_command(command):
    pass_pairs = []
    pass_pattern = r'(([0-9]*) pass ([0-9]*))'
    matches = re.findall(pass_pattern, command)
    for m in matches:
        pass_pairs.append((int(m[1]), int(m[2])))

    return pass_pairs


def _update_time(msg, state: PlayerState):
    comp_re = re.compile("\\([^(]* ({0})".format(_SIGNED_INT_REGEX))
    state.world_view.sim_time = int(re.match(comp_re, msg).group(1))


def parse_message_trainer(msg: str, world_view: WorldViewCoach):
    if msg.startswith("(error"):
        print("Trainer received error: {0}".format(msg))
        return
    # The server_param and player_param files do not contain a time stamp
    # Can be used to get the configuration of the server and player
    # server_param: clang_mess_per_cycle, olcoach_port = 6002 etc.
    # player_param: General parameters of players, like max substitutions etc.
    # player_type: The current player type and its stats, like max_speed, kick power etc.
    if msg.startswith("(server_param") or msg.startswith("(player_param") or msg.startswith("(player_type"):
        if msg.startswith("(server_param"):
            print(msg)
        return

    if msg.startswith("(hear"):
        _parse_hear_coach(msg, world_view)
    elif msg.startswith("(init"):
        # Init contains no information for trainer
        return
    elif msg.startswith("(ok look") or msg.startswith("(see_global"):
        _parse_ok_look_online_coach(msg, world_view)
        # Update time
        comp_re = re.compile("\\([^(]* ({0})".format(_SIGNED_INT_REGEX))
        world_view.sim_time = int(re.match(comp_re, msg).group(1))
    elif msg.startswith("(change_player_type"):
        # (change player type UNUM TYPE) if team player changed type. (change player type UNUM) if opponent player
        # changed type. The type is not disclosed by the opponent team.
        return
    elif msg.startswith("(clang"):
        # The players tell the coach which versions of commands they support.
        # Example: (clang (ver (p "Team1" 6) 7 16))
        return
    elif msg.startswith("(ok eye") or msg.startswith("(ok"):
        # (ok for general confirmations
        # Simple confirmation, that vision mode was changed
        return
    else:
        raise Exception("Unknown message received: " + msg)


def parse_message_online_coach(msg: str, team: str, world_view: WorldViewCoach):
    if msg.startswith("(error"):
        print("Coach for team {0} received error: {1}".format(team, msg))
        return
    # The server_param and player_param files do not contain a time stamp
    # Can be used to get the configuration of the server and player
    # server_param: clang_mess_per_cycle, olcoach_port = 6002 etc.
    # player_param: General parameters of players, like max substitutions etc.
    # player_type: The current player type and its stats, like max_speed, kick power etc.
    if msg.startswith("(server_param") or msg.startswith("(player_param") or msg.startswith("(player_type"):
        if msg.startswith("(server_param"):
            print(msg)
        return

    if msg.startswith("(hear"):
        _parse_hear_coach(msg, world_view)
    elif msg.startswith("(init"):
        _parse_init_online_coach(msg, world_view)
    elif msg.startswith("(ok look") or msg.startswith("(see_global"):
        _parse_ok_look_online_coach(msg, world_view)
        # Update time
        comp_re = re.compile("\\([^(]* ({0})".format(_SIGNED_INT_REGEX))
        world_view.sim_time = int(re.match(comp_re, msg).group(1))
    elif msg.startswith("(change_player_type"):
        # (change player type UNUM TYPE) if team player changed type. (change player type UNUM) if opponent player
        # changed type. The type is not disclosed by the opponent team.
        return
    elif msg.startswith("(clang"):
        # The players tell the coach which versions of commands they support.
        # Example: (clang (ver (p "Team1" 6) 7 16))
        return
    elif msg.startswith("(ok eye") or msg.startswith("(ok"):
        # (ok for general confirmations
        # Simple confirmation, that vision mode was changed
        return
    else:
        raise Exception("Unknown message received: " + msg)


def parse_message_update_state(msg: str, ps: PlayerState):
    if msg.startswith("(error"):
        print("Player num {0}, team {1}, received error: {2}".format(ps.num, ps.team_name, msg))
        return
    # The server_param and player_param files do not contain a time stamp
    # Can be used to get the configuration of the server and player
    # server_param: clang_mess_per_cycle, olcoach_port = 6002 etc.
    # player_param: General parameters of players, like max substitutions etc.
    # player_type: The current player type and its stats, like max_speed, kick power etc.
    # ok clang is just an ok message, that the coach language requested has been accepted.
    if not (msg.startswith("(server_param") or msg.startswith("(player_param") or msg.startswith("(player_type")
            or msg.startswith("(ok clang")):
        pass
        # _update_time(msg, ps)

    if msg.startswith("(hear"):
        _parse_hear(msg, ps)
    elif msg.startswith("(sense_body"):
        _update_time(msg, ps)
        _parse_body_sense(msg, ps)
    elif msg.startswith("(init"):
        _parse_init(msg, ps)
    elif msg.startswith("(see "):
        last_update = ps.action_history.last_see_update
        if ps.world_view.game_state == 'play_on' and msg.startswith("(see {0}".format(last_update)):
            return  # Discard duplicate messages

        _update_time(msg, ps)
        _parse_see(msg, ps)
        ps.on_see_update()

    elif msg.startswith("(server_param") or msg.startswith("(player_param") or msg.startswith("(player_type"):
        return
    elif msg.startswith("(change_player_type"):
        # (change player type UNUM TYPE) if team player changed type. (change player type UNUM) if opponent player
        # changed type. The type is not disclosed by the opponent team.
        return
    elif msg.startswith("(ok clang"):
        # Simply a confirmation, that the requested coach language was accepted
        return
    else:
        raise Exception("Unknown message received: " + msg)


'''
Old protocol 3: 
(see 0 ((flag c) 50.4 -25) ((flag c b) 47 14) ((flag r t) 113.3 -29) ((flag r b) 98.5 7) ((flag g r b) " \
"99.5 -8) ((goal r) 100.5 -12) ((flag g r t) 102.5 -16) ((flag p r b) 81.5 -1) ((flag p r c) 84.8 -15) ((" \
"flag p r t) 91.8 -27) ((flag p l b) 9.7 -10 0 0) ((ball) 49.4 -25) ((player) 44.7 -24) ((player Team1 5) " \
"30 -41 0 0) ((player Team1) 33.1 -5) ((player Team1) 44.7 -28) ((player Team1) 44.7 -24) ((player Team1) " \
"40.4 -2) ((player) 60.3 7) ((player) 60.3 -16) ((player) 66.7 -20) ((player) 60.3 -31) ((player) 90 -39) (" \
"(player) 99.5 -9) ((player) 66.7 -10) ((player) 66.7 -21) ((player) 99.5 -19) ((player) 90 6) ((player) " \
"60.3 -27) ((line r) 98.5 90))

New protocol 7-16:
"(see 0 ((f r t) 55.7 3) ((f g r b) 70.8 38) ((g r) 66.7 34) ((f g r t) 62.8 28) ((f p r c) 53.5 43) ((f p " \
"r t) 42.5 23) ((f t 0) 3.6 -34 0 0) ((f t r 10) 13.2 -9 0 0) ((f t r 20) 23.1 -5 0 0) ((f t r 30) 33.1 -3 " \
"0 0) ((f t r 40) 42.9 -3) ((f t r 50) 53 -2) ((f r 0) 70.8 31) ((f r t 10) 66 24) ((f r t 20) 62.8 16) ((f " \
"r t 30) 60.9 7) ((f r b 10) 76.7 38) ((f r b 20) 83.1 43) ((p) 66.7 35) ((p \"Team2\" 2) 9 0 0 0 0 0) ((p " \
"\"Team2\" 3) 12.2 0 0 0 0 0) ((p \"Team2\" 4) 14.9 0 0 0 0 0) ((p \"Team2\" 5) 18.2 0 0 0 0 0) ((p " \
"\"Team2\" 6) 20.1 0 0 0 0 0) ((p \"Team2\" 7) 24.5 0 0 0 0 0) ((p \"Team2\") 27.1 0) ((p \"Team2\" 9) 30 0 " \
"0 0 0 0) ((p \"Team2\") 33.1 0) ((p \"Team2\") 36.6 0)) "
'''


def _parse_see(msg, ps: player.PlayerState):
    regex2 = re.compile(_SEE_MSG_REGEX)
    matches = regex2.findall(msg)

    flag_strings = []
    players = []
    goals = []
    lines = []
    ball = None
    for element in matches:
        if str(element).startswith("((f") or str(element).startswith("((F"):
            flag_strings.append(element)
        elif str(element).startswith("((g") or str(element).startswith("((G"):
            goals.append(element)
        elif str(element).startswith("((p") or str(element).startswith("((P"):
            players.append(element)
        elif str(element).startswith("((l") or str(element).startswith("((L"):
            lines.append(element)
        elif str(element).startswith("((b") or str(element).startswith("((B"):
            ball = element
        else:
            raise Exception("Unknown see element: " + str(element))

    flags = create_flags(flag_strings, ps)

    _approx_position(flags, ps)
    _approx_body_angle(flags, ps)
    _parse_players(players, ps)
    _parse_goals(goals, ps)
    _parse_ball(ball, ps)
    _parse_lines(lines, ps)


def _parse_lines(lines, ps):
    for line in lines:
        if str(line).startswith("((L"):
            continue
        else:
            _parse_line(line, ps)


def _parse_line(text: str, ps: PlayerState):
    line_regex = "\\(\\(l (r|l|b|t)\\)\\s({0}) ({1})".format(_REAL_NUM_REGEX, _SIGNED_INT_REGEX)
    regular_expression = re.compile(line_regex)
    matched = regular_expression.match(text)

    line_side = matched.group(1)
    line_distance = matched.group(2)
    line_relative_angle = matched.group(3)

    # Add information to WorldView
    new_line = world_objects.Line(line_side=line_side, distance=line_distance, relative_angle=line_relative_angle)
    ps.world_view.lines.append(new_line)
    return matched


def _parse_goals(goals, ps):
    for goal in goals:
        _parse_goal(goal, ps)


def _parse_goal(text: str, ps: PlayerState):
    # Unknown see object (out of field of view)
    if text.startswith("((G"):
        return world_objects.Goal(None, None, None)

    goal_regex = "\\(\\(g (r|l)\\)\\s({0}) ({1})".format(_REAL_NUM_REGEX, _SIGNED_INT_REGEX)
    regular_expression = re.compile(goal_regex)
    matched = regular_expression.match(text)

    goal_side = matched.group(1)
    goal_distance = matched.group(2)
    goal_relative_angle = matched.group(3)

    # Add information to WorldView
    new_goal = world_objects.Goal(goal_side=goal_side, distance=goal_distance, relative_angle=goal_relative_angle)
    ps.world_view.goals.append(new_goal)
    return matched


class Flag:

    def __init__(self, identifier, coordinate, distance, direction) -> None:
        self.identifier = identifier
        self.coordinate = coordinate
        self.relative_distance = distance
        self.body_relative_direction = direction

    def __repr__(self) -> str:
        return "Flag " + self.identifier + " : " + str(self.coordinate) + ", dist: " + str(self.relative_distance) + \
               ", direction: " + str(self.body_relative_direction)


def create_flags(flag_strings, state: PlayerState):
    known_flags_strings = []

    # Remove flags out of field of view
    for flag in flag_strings:
        if not str(flag).startswith("((F)"):
            known_flags_strings.append(flag)

    ids = _extract_flag_identifiers(known_flags_strings)
    coords = _extract_flag_coordinates(ids)
    distances = _extract_flag_distances(known_flags_strings)
    directions = _extract_flag_directions(known_flags_strings, state.body_state.neck_angle)

    flags = []

    for i in range(len(known_flags_strings)):
        flags.append(Flag(ids[i], coords[i], float(distances[i]), float(directions[i])))

    return flags


def _approx_body_angle(flags: [Flag], state):
    if not state.position.is_value_known():
        return

    estimated_angles = []
    # angle between c1 and c2, with c3 offsetting to make 0 degrees in some direction
    # For this purpose x+ = east, -x = west etc.
    player_coord = state.position.get_value()
    for flag in flags:
        radians_between_flag_player = calculate_full_origin_angle_radians(flag.coordinate, player_coord)
        flag_body_angle = float(radians_between_flag_player) - math.radians(float(flag.body_relative_direction))
        estimated_body_angle = math.degrees(flag_body_angle) % 360

        estimated_angles.append(estimated_body_angle)

    mean_angle = find_mean_angle(estimated_angles, acceptable_variance=3.0)

    if mean_angle is not None:
        new_body_angle = mean_angle % 360
        new_neck_angle = state.body_state.neck_angle

        # Detect if latest turn has been included in this see update
        if state.action_history.turn_in_progress:
            # otherwise, see if new angle matches expected one
            old_body_angle = state.body_angle.get_value()
            old_neck_angle = state.last_see_global_angle - old_body_angle

            expected_neck_angle = state.action_history.expected_neck_angle
            expected_body_angle = state.action_history.expected_body_angle

            actual_body_delta = abs(smallest_angle_difference(old_body_angle, new_body_angle))
            actual_neck_delta = abs(smallest_angle_difference(old_neck_angle, new_neck_angle))

            if expected_body_angle is None:
                expected_body_delta = actual_body_delta  # No body turn is expected
            else:
                expected_body_delta = abs(smallest_angle_difference(old_body_angle, expected_body_angle))

            if expected_neck_angle is None:
                expected_neck_delta = actual_neck_delta  # No neck turn is expected
            else:
                expected_neck_delta = abs(smallest_angle_difference(old_neck_angle, expected_neck_angle))

            if (actual_body_delta >= expected_body_delta / 2 and actual_neck_delta >= expected_neck_delta / 2) or \
                    state.action_history.missed_turn_last_see:
                # We have turned at least half of what was expected,
                # or we have received more than one see update since turn,
                # so we assume the turn was included
                state.action_history.turn_in_progress = False
                state.action_history.missed_turn_last_see = False
                state.action_history.expected_body_angle = None
                state.action_history.expected_neck_angle = None
            else:
                # No significant turn has been detected since last see update,
                # so the turn is assumed to have been missed
                debug_msg(str(state.now()) + "Turn missed in see update! (expected,actual) body : " + str(expected_body_delta) +
                          str(actual_body_delta) + " neck: " + str(expected_neck_delta) + str(actual_neck_delta), "POSITIONAL")
                state.action_history.turn_in_progress = True
                state.action_history.missed_turn_last_see = True

        state.last_see_global_angle = (mean_angle + state.body_state.neck_angle) % 360
        state.update_body_angle(mean_angle, state.now())
        # state.body_angle.set_value(mean_angle, state.position.last_updated_time)
    else:
        debug_msg("No angle could be found", "POSITIONAL")


# ((flag g r b) 99.5 -5)
# ((flag p l c) 27.1 10 -0 0)
# distance, direction, dist_change, dir_change
def _extract_flag_directions(flag_strings, neck_angle):
    flag_directions = []
    for flag_string in flag_strings:
        # Remove the first part of the string *((flag p l c)*
        removed_flag_name = flag_string.split(') ', 1)[1]
        # Remove ) from the items
        cur_flag = str(removed_flag_name).replace(")", "")
        cur_flag = str(cur_flag).replace("(", "")

        split_by_whitespaces = []
        split_by_whitespaces = re.split('\\s+', cur_flag)

        # We now have a list of elements like this:
        # ['13.5', '-31', '2', '-5']

        direction = float(split_by_whitespaces[1])
        direction += neck_angle  # Account for neck angle
        direction %= 360
        flag_directions.append(direction)
    return flag_directions


# Input ((b) 13.5 -31 0 0)
# or ((b) 44.7 -20)
# Or ((B) distance direction)
# distance, direction, dist_change, dir_change
def _parse_ball(ball: str, ps: player.PlayerState):
    # If ball is not present at all or only seen behind the player
    if ball is None:
        return

    # Remove ) from the items
    ball = str(ball).replace(")", "")
    ball = str(ball).replace("(", "")

    split_by_whitespaces = []
    split_by_whitespaces = re.split('\\s+', ball)

    # We now have a list of elements like this:
    # ['b', '13.5', '-31', '2', '-5']

    # These are always included
    distance = float(split_by_whitespaces[1])
    direction = int(split_by_whitespaces[2])
    # direction += ps.body_state.neck_angle # Accommodates non-zero neck angles
    # direction %= 360
    # These might be included depending on the distance and view of the player
    distance_chng = PrecariousData.unknown()
    dir_chng = PrecariousData.unknown()

    # If we also know dist_change and dir_change
    if len(split_by_whitespaces) > 3:
        distance_chng = split_by_whitespaces[3]
        dir_chng = split_by_whitespaces[4]

    # print("Pretty: Distance ({0}), Direction ({1}), distance_chng ({2}), dir_chng ({3})".format(distance, direction,
    #                                                                                            distance_chng,
    #                                                                                            dir_chng))
    ball_coord = None
    # The position of the ball can only be calculated, if the position of the player is known
    if ps.position.is_value_known() and ps.get_global_angle().is_value_known():
        pos: Coordinate = ps.position.get_value()
        ball_coord: Coordinate = get_object_position(object_rel_angle=int(direction), dist_to_obj=float(distance),
                                                     my_x=pos.pos_x,
                                                     my_y=pos.pos_y,
                                                     my_global_angle=ps.get_global_angle().get_value())

        # Save old ball information
        old_position_history = None
        old_dist_history = None
        if ps.world_view.ball.is_value_known():
            old_position_history = ps.world_view.ball.get_value().position_history
            old_dist_history = ps.world_view.ball.get_value().dist_history

        new_ball = Ball(distance=distance, direction=direction, coord=ball_coord,
                        pos_history=old_position_history, time=ps.now(), dist_history=old_dist_history)

        ps.update_ball(new_ball, ps.now())


# Parse this: (p "team"? num? goalie?)
# Returns arguments in this order: team, num, is_goalie
def _parse_player_obj_name(obj_name, ps: player.PlayerState):
    # Remove "noise" in form of " and ( from the object name
    obj_name = str(obj_name).replace("(", "")
    obj_name = str(obj_name).replace("\"", "")

    # Split by whitespaces to get a divided list like so:
    # ['p', '"Team2"', '7']
    split_by_whitespaces = re.split('\\s+', obj_name)

    # If we have no info on who the player is
    if len(split_by_whitespaces) == 1:
        return None, None, None

    # If we know the team of the player
    if len(split_by_whitespaces) == 2:
        return split_by_whitespaces[1], None, None

    # If we know both team and player_num
    if len(split_by_whitespaces) == 3:
        return split_by_whitespaces[1], split_by_whitespaces[2], None

    # If we know both the team, player_num and that the player is the goalie
    if len(split_by_whitespaces) == 4:
        return split_by_whitespaces[1], split_by_whitespaces[2], True


# (b) 0 0 0 0)
# X Y DELTAX DELTAY
def _parse_ball_online_coach(ball, wv: WorldViewCoach):
    my_ball = ball

    # Remove ),( and " from the items
    my_ball = str(my_ball).replace(")", "")
    my_ball = str(my_ball).replace("(", "")

    # This gives us a list like:
    # ['b', '0', '0', '0', '0']
    split_by_whitespaces = re.split('\\s+', my_ball)

    x = float(split_by_whitespaces[1])
    y = float(split_by_whitespaces[2])
    delta_x = float(split_by_whitespaces[3])
    delta_y = float(split_by_whitespaces[4])

    coord = Coordinate(x, y)

    new_ball = BallOnlineCoach(coord=coord, delta_x=delta_x, delta_y=delta_y)
    wv.ball = new_ball


# (ok look 926 ((g r) 52.5 0) ((g l) -52.5 0) ((b) 0 0 0 0) ((p "Team1" 1 goalie) 33.9516 -18.3109 -0.0592537 0.00231559 -180 0) ((p "Team2" 1 goalie) 50 0 0 0 0 0))
def _parse_ok_look_online_coach(msg, wv: WorldViewCoach):
    regex2 = re.compile(_SEE_MSG_REGEX)
    matches = regex2.findall(msg)

    players = []
    goals = []
    ball = None
    for element in matches:
        if str(element).startswith("((p") or str(element).startswith("((P"):
            players.append(element)
        elif str(element).startswith("((b") or str(element).startswith("((B"):
            ball = element
        elif str(element).startswith("((g") or str(element).startswith("((G"):
            continue
        else:
            raise Exception("Unknown see element: " + str(element))

    _parse_ball_online_coach(ball, wv)
    _parse_players_online_coach(players, wv)


# ((p "Team1" 1 goalie) 33.9516 -18.3109 -0.0592537 0.00231559 -180 0) ((p "Team2" 1 goalie) 50 0 0 0 0 0)
# ((p "team" num goalie?) X Y DELTAX DELTAY BODYANGLE NECKANGLE [POINTING DIRECTION]
def _parse_players_online_coach(players: [], wv: WorldViewCoach):
    # Remove old view of players
    wv.players.clear()
    # ((p "Team1" 1) -50 0 0 0 0 0)
    for cur_player in players:
        team = None
        num = None
        is_goalie = False
        coord: Coordinate = None
        delta_x = None
        delta_y = None
        body_angle = None
        neck_angle = None
        pointing_direction = None

        # Remove ),( and " from the items
        cur_player = str(cur_player).replace(")", "")
        cur_player = str(cur_player).replace("(", "")
        cur_player = str(cur_player).replace("\"", "")

        # This gives us a list like this:
        # ['p', 'Team1', '1', 'goalie', '-50', '0', '0', '0', '0', '0']
        # Todo include pointing direction? - Philip
        split_by_whitespaces = re.split('\\s+', cur_player)

        for s in split_by_whitespaces:
            if s == "k" or s == "t":
                split_by_whitespaces.remove(s)

        is_goalie_included = 0
        if len(split_by_whitespaces) >= 10:
            is_goalie = True
            is_goalie_included = 1

        team = split_by_whitespaces[1]
        num = split_by_whitespaces[2]
        x = float(split_by_whitespaces[3 + is_goalie_included])
        y = float(split_by_whitespaces[4 + is_goalie_included])
        delta_x = float(split_by_whitespaces[5 + is_goalie_included])
        delta_y = float(split_by_whitespaces[6 + is_goalie_included])
        coord: Coordinate = Coordinate(x, y)
        body_angle = split_by_whitespaces[7 + is_goalie_included]
        body_angle = int(body_angle) % 360
        neck_angle = split_by_whitespaces[8 + is_goalie_included]
        neck_angle = int(neck_angle) % 360

        other_player = PlayerViewCoach(team=team, num=num, coord=coord, delta_x=delta_x, delta_y=delta_y
                                       , body_angle=body_angle, neck_angle=neck_angle, is_goalie=is_goalie
                                       , has_ball=False)

        wv.players.append(other_player)

    # Reset possession
    for play in wv.players:
        play.has_ball = False

    # Find closest player to ball
    if len(wv.get_closest_players_to_ball(1)) < 0:
        possessor: PlayerViewCoach = wv.get_closest_players_to_ball(1)[0]
        # If closest player less than 1 meter away from ball, give possession.
        if possessor.coord.euclidean_distance_from(wv.ball.coord) < 1:
            possessor.has_ball = True


# ((p "team"? num?) Distance Direction DistChng? DirChng? BodyFacingDir? HeadFacingDir? [PointDir]?)
# ((p "Team1" 5) 30 -41 0 0)
# 1: (ObjName Distance Direction DistChange DirChange BodyFacingDir HeadFacingDir [PointDir] [t] [k]])
# 2: (ObjName Distance Direction DistChange DirChange [PointDir] [t] [k]])
# 3: (ObjName Distance Direction)
# 4: (ObjName Direction)
def _parse_players(players: [], ps: player.PlayerState):
    ps.players_close_behind = 0
    for cur_player in players:
        # Unknown see object (out of field of view)
        if cur_player.startswith("((P"):
            ps.players_close_behind += 1
            continue
        # Default values
        team = None
        num = None
        is_goalie = None
        distance = None
        direction = None
        dist_chng = None
        dir_chng = None
        body_dir = None
        head_dir = None

        # Get object name like (player Team1 5) or (player Team1 5 goalie)
        obj_name = re.split('\\)+', cur_player)[0]
        team, num, is_goalie = _parse_player_obj_name(obj_name, ps)

        # The rest of the player like 9 0 0 0 0 0
        # Start from index 1 to remove a white space
        cur_player = re.split('\\)+', cur_player)[1][1:]

        # Remove ),( and " from the items
        cur_player = str(cur_player).replace(")", "")
        cur_player = str(cur_player).replace("(", "")
        cur_player = str(cur_player).replace("\"", "")

        split_by_whitespaces = re.split('\\s+', cur_player)

        for s in split_by_whitespaces:
            if s == "t" or s == "k":
                split_by_whitespaces.remove(s)

        # We now have a list of elements like this:
        # Diretion DistChange DirChange BodyFacingDir HeadFacingDir [PointDir]
        # ['30', '-41', '0', '0' ]

        # If only direction
        if len(split_by_whitespaces) == 1:
            # We don't save states of players without distance
            continue
        # If only distance and direction
        elif len(split_by_whitespaces) == 2:
            distance = float(split_by_whitespaces[0])
            direction = float(split_by_whitespaces[1])
        # If Distance Direction DistChange DirChange
        elif len(split_by_whitespaces) == 4:
            distance = float(split_by_whitespaces[0])
            direction = float(split_by_whitespaces[1])
            dist_chng = split_by_whitespaces[2]
            dir_chng = split_by_whitespaces[3]
        # If Distance Direction DistChange DirChange BodyFacingDir HeadFacingDir [PointDir]
        elif len(split_by_whitespaces) >= 6:
            distance = float(split_by_whitespaces[0])
            direction = float(split_by_whitespaces[1])
            dist_chng = split_by_whitespaces[2]
            dir_chng = split_by_whitespaces[3]
            body_dir = float(split_by_whitespaces[4])
            head_dir = float(split_by_whitespaces[5])

        my_pos: Coordinate = ps.position.get_value()
        other_player_coord = PrecariousData.unknown()

        direction += ps.body_state.neck_angle  # Accommodates non-zero neck-angles

        if ps.position.is_value_known():
            other_player_coord = get_object_position(object_rel_angle=direction, dist_to_obj=distance,
                                                     my_x=my_pos.pos_x, my_y=my_pos.pos_y,
                                                     my_global_angle=ps.body_angle.get_value())

        new_player = ObservedPlayer(team=team, num=num, distance=distance, direction=direction, dist_chng=dist_chng
                                    , dir_chng=dir_chng, body_dir=body_dir, head_dir=head_dir, is_goalie=is_goalie
                                    , coord=other_player_coord)

        ps.world_view.update_player_view(new_player)


def _parse_init_online_coach(msg, wv: WorldViewCoach):
    regex = re.compile("\\(init ([lr]) .*\\)")
    matched = regex.match(msg)
    wv.side = matched.group(1)


def _parse_init(msg, ps: player.PlayerState):
    regex = re.compile("\\(init ([lr]) ([0-9]*)")
    matched = regex.match(msg)
    ps.world_view.side = matched.group(1)
    ps.num = int(matched.group(2))


def _parse_hear_coach(text: str, coach_world_view):
    split_by_whitespaces = re.split('\\s+', text)

    sender = split_by_whitespaces[2]
    if sender == "referee":
        regex_string = "\\(hear ({0}) referee ({1})\\)".format(_SIGNED_INT_REGEX, _ROBOCUP_MSG_REGEX)

        regular_expression = re.compile(regex_string)
        matched = regular_expression.match(text)

        coach_world_view.game_state = matched.group(2)

        return
    elif sender == "self":
        return
    elif sender == "online_coach_left":
        return
    elif sender == "online_coach_right":
        return
    elif sender == "coach":
        return
    else:
        regex_string = "\\(hear ({0}) ({0}) ({1})\\)".format(_SIGNED_INT_REGEX, _ROBOCUP_MSG_REGEX)

        regular_expression = re.compile(regex_string)
        matched = regular_expression.match(text)

        return


# Three different modes
# example: (hear 0 referee kick_off_l)
# example: (hear 0 self *msg*)
# Pattern: (hear *time* *degrees* *msg*)
def _parse_hear(text: str, ps: PlayerState):
    split_by_whitespaces = re.split('\\s+', text)
    # time = int(split_by_whitespaces[1])
    # ps.world_view.sim_time = time  # Update players understanding of time
    sender = split_by_whitespaces[2]
    if sender == "referee":
        regex_string = "\\(hear ({0}) referee ({1})\\)".format(_SIGNED_INT_REGEX, _ROBOCUP_MSG_REGEX)

        regular_expression = re.compile(regex_string)
        matched = regular_expression.match(text)

        ps.world_view.game_state = matched.group(2)

        return
    elif sender == "self":
        return
    elif sender == "online_coach_left":
        if ps.world_view.side == "l":
            coach_command_pattern = '.*"(.*)".*'
            matches = re.match(coach_command_pattern, text)
            ps.coach_command.set_value(matches.group(1), 0)  # todo Time?
    elif sender == "online_coach_right":
        return  # todo handle incoming messages from online coach
    elif sender == "coach":
        return  # todo handle trainer input
    else:
        regex_string = "\\(hear ({0}) ({0}) ({1})\\)".format(_SIGNED_INT_REGEX, _ROBOCUP_MSG_REGEX)

        regular_expression = re.compile(regex_string)
        matched = regular_expression.match(text)

        return


# example : (sense_body 0 (view_mode high normal) (stamina 8000 1 130600) (speed 0 0) (head_angle 0) (kick 0)
# (dash 0) (turn 0) (say 0) (turn_neck 0) (catch 0) (move 0) (change_view 0) (arm (movable 0) (expires 0) (target 0 0)
# (count 0)) (focus (target none) (count 0)) (tackle (expires 0) (count 0)) (collision none) (foul  (charged 0)
# (card none)))

# ALL COUNT COMMANDS MEAN: HOW MANY TIMES THE COMMAND HAS BEEN EXECUTED BY THE PLAYER SO FAR
# Group [1] = time,
# [2] = view mode,
# [3] = stamina, [4] = effort, [5] = capacity,
# [6] = speed, [7] = direction of speed,
# [8] = head angle,
# [9] = kick count,
# [10] = dash count,
# [11] = turn count,
# [12] = say count,
# [13] = turn neck count,
# [14] = catch count,
# [15] = move count,
# [16] = change view count,
# [17] = movable cycles, [18] = expire cycles, [19] = distance, [20] = direction, [21] = point to count
# [22] = target, [23] = Unum, [24] = count,
# [25] = expire cycles, [26] count,
# [27] = collision,
# [28] = charged, [29] = card

def _parse_body_sense(text: str, state: PlayerState):
    if "collision (ball" in text:
        state.ball_collision_time = state.now()
    regex_string = ".*sense_body ({1}).*view_mode ({2})\\).*stamina ({0}) ({0}) ({0})\\).*speed ({0}) ({1})\\)"
    regex_string += ".*head_angle ({1})\\).*kick ({1})\\).*dash ({1})\\).*turn ({1})\\)"
    regex_string += ".*say ({1})\\).*turn_neck ({1})\\).*catch ({1})\\).*move ({1})\\).*change_view ({1})\\)"
    regex_string += ".*movable ({1})\\).*expires ({1})\\).*target ({1}) ({1})\\).*count ({1})\\)\\)"
    regex_string += ".*target (none|l|r)( {1})?\\).*count ({1})\\)\\)"
    regex_string += ".*expires ({1})\\).*count ({1})\\)"
    regex_string += ".*collision (none|{2})\\).*charged ({1})\\).*card (red|yellow|none)\\)\\)\\)"
    regex_string = regex_string.format(_REAL_NUM_REGEX, _SIGNED_INT_REGEX, _ROBOCUP_MSG_REGEX)

    regular_expression = re.compile(regex_string)
    matched = regular_expression.match(text)

    '''
    if matched.group(23) is None: # todo Does not not work when no groups are present
        print(text)
        unum = "none"
    else:
        unum = int(matched.group(23))
    '''

    # ps.body_state.time = int(matched.group(1))
    state.body_state.view_mode = matched.group(2)
    state.body_state.stamina = float(matched.group(3))
    state.body_state.effort = float(matched.group(4))
    state.body_state.capacity = float(matched.group(5))

    expected_speed = state.action_history.expected_speed
    if expected_speed is not None:
        state.body_state.speed = expected_speed
        state.action_history.expected_speed = None
    else:
        state.body_state.speed = float(matched.group(6))



    state.body_state.direction_of_speed = int(matched.group(7))
    state.body_state.neck_angle = int(matched.group(8))
    state.body_state.arm_movable_cycles = int(matched.group(17))
    state.body_state.arm_expire_cycles = int(matched.group(18))
    state.body_state.distance = float(matched.group(19))
    state.body_state.direction = int(matched.group(20))
    state.body_state.target = matched.group(22)
    state.body_state.tackle_expire_cycles = int(matched.group(25))
    state.body_state.collision = matched.group(27)
    state.body_state.charged = int(matched.group(28))
    state.body_state.card = matched.group(29)

    return matched


# Example : (see 0 ((f r b) 48.9 29) ((f g r b) 42.5 -4) ((g r) 43.8 -13) ((f g r t) 45.6 -21)
#           ((f p r b) 27.9 21) ((f p r c) 27.9 -21 0 0) ((P) 1 -179) ((p Team2 2) 1 0 0 0)
#           ((P) 0.5 151) ((p Team2 4) 0.5 -28 0 0) ((l r) 42.5 90))
def _parse_flags(text):
    flag_regex = "\\(f [^)]*\\) {0} {0}".format(_REAL_NUM_REGEX)
    return re.findall(flag_regex, text)


def _match(regex_string, text):
    regular_expression = re.compile(regex_string)
    regex_match = regular_expression.match(text)
    return regex_match


def _extract_flag_identifiers(flags):
    flag_identifiers_regex = ".*\\(f ([^\\)]*)\\)"
    flag_identifiers = []
    for flag in flags:
        m = _match(flag_identifiers_regex, flag)
        flag_identifiers.append(m.group(1).replace(" ", ""))
    return flag_identifiers


def _extract_flag_distances(flags):
    flag_distance_regex = ".*\\(f [^\\)]*\\) ({0}) ".format(_REAL_NUM_REGEX)
    flag_distances = []
    for flag in flags:
        m = _match(flag_distance_regex, flag)
        flag_distances.append(m.group(1).replace(" ", ""))
    return flag_distances


def _extract_flag_coordinates(flag_ids):
    coords = []
    for flag_id in flag_ids:
        coord_pair = _FLAG_COORDS.get(flag_id)
        coords.append(Coordinate(coord_pair[0], coord_pair[1]))
    return coords


def _zip_flag_coords_distance(flags):
    flag_ids = _extract_flag_identifiers(flags)
    flag_coords = _extract_flag_coordinates(flag_ids)
    flag_distances = _extract_flag_distances(flags)

    return zip(flag_coords, flag_distances)


def _calculate_distance(coord1, coord2):
    x_dist = abs(coord1.pos_x - coord2.pos_x)
    y_dist = abs(coord1.pos_y - coord2.pos_y)
    return sqrt(pow(float(x_dist), 2) + pow(float(y_dist), 2))


# Calculates position as two possible offsets from flag_one
def _trilaterate_offset(flag_one, flag_two):
    distance_between_flags = _calculate_distance(flag_one.coordinate, flag_two.coordinate)

    x = (((flag_one.relative_distance ** 2) - (flag_two.relative_distance ** 2)) + (distance_between_flags ** 2)) \
        / (2.0 * distance_between_flags)

    # Not sure if this is a correct solution
    if abs(flag_one.relative_distance) > abs(x):
        y = sqrt((flag_one.relative_distance ** 2) - (x ** 2))
    else:
        y = sqrt(pow(x, 2.0) - pow(flag_one.relative_distance, 2.0))

    # This calculation provides two possible offset solutions (x, y) and (x, -y)
    return Coordinate(x, y), Coordinate(x, -y)


def _solve_trilateration(flag_1, flag_2):
    (possible_offset_1, possible_offset_2) = _trilaterate_offset(flag_1, flag_2)
    # The trilateration algorithm assumes horizontally aligned flags
    # To resolve this, the solution is calculated as if the flags were horizontally aligned
    # and is then rotated to match the actual angle
    radians_to_rotate = calculate_smallest_origin_angle_between(flag_1.coordinate, flag_2.coordinate)
    corrected_offset_from_flag_one_1 = rotate_coordinate(possible_offset_1, radians_to_rotate)
    corrected_offset_from_flag_one_2 = rotate_coordinate(possible_offset_2, radians_to_rotate)

    return flag_1.coordinate - corrected_offset_from_flag_one_1, flag_1.coordinate - corrected_offset_from_flag_one_2


def _get_all_combinations(original_list):
    combinations = []

    for i in range(0, len(original_list) - 1):
        for j in range(i + 1, len(original_list)):
            combinations.append((original_list[i], original_list[j]))

    return combinations


def _find_all_solutions(flags: [Flag]):
    solutions = []
    flag_combinations = _get_all_combinations(flags)
    for combination in flag_combinations:
        possible_solutions = _solve_trilateration(combination[0], combination[1])
        solutions.append(possible_solutions[0])
        solutions.append(possible_solutions[1])
    return solutions


def _average_point(cluster):
    amount_of_clusters = len(cluster)
    total_x = 0
    total_y = 0

    for point in cluster:
        total_x += point.pos_x
        total_y += point.pos_y

    return Coordinate(total_x / amount_of_clusters, total_y / amount_of_clusters)


def _find_mean_solution(all_solutions, state):
    amount_of_correct_solutions = (len(all_solutions) * (len(all_solutions) - 1)) / 2
    acceptable_distance = 3.0
    cluster_size_best_solution = 0
    best_cluster = []

    for solution1 in all_solutions:
        if not is_possible_position(solution1, state):
            continue
        cluster = [solution1]

        for solution2 in all_solutions:
            if solution1 == solution2:
                continue

            if solution1.euclidean_distance_from(solution2) < acceptable_distance:
                cluster.append(solution2)

            if len(cluster) >= amount_of_correct_solutions:
                return _average_point(cluster)

        if len(cluster) > cluster_size_best_solution:
            cluster_size_best_solution = len(cluster)
            best_cluster = cluster

    if len(best_cluster) == 0:
        return None
    return _average_point(best_cluster)


def is_possible_position(new_position: Coordinate, state: PlayerState):
    if not world_objects.is_inside_field_bounds(new_position):
        return False

    # If the timer is not running (ie. game mode != play_on) players can be teleported around
    if state.position.last_updated_time == state.now():
        return True

    # If no information on previous state exists, then all positions inside the field are possible positions
    if not state.position.is_value_known(state.world_view.sim_time - 5):
        return True

    ticks_since_update = state.world_view.sim_time - state.position.last_updated_time
    possible_travel_distance = (player.MAX_MOVE_DISTANCE_PER_TICK + 1.0) * ticks_since_update
    return possible_travel_distance >= new_position.euclidean_distance_from(state.position.get_value())


def furthest_flag_distance_and_index(flags: [Flag]):
    furthest_flag = flags[0]
    furthest_dist = furthest_flag.relative_distance
    furthest_index = 0

    for i, flag in enumerate(flags[1:]):
        dist = flag.relative_distance
        if dist > furthest_dist:
            furthest_index = i
            furthest_dist = dist

    return furthest_dist, furthest_index


def find_closest_flags(flags, amount):
    closest_flags = flags[0:amount]
    furthest_dist_closest_flags, furthest_index = furthest_flag_distance_and_index(closest_flags)

    i = amount
    while i < len(flags):
        f = flags[i]
        f_dist = f.relative_distance
        if f_dist < furthest_dist_closest_flags:
            closest_flags[furthest_index] = f
            # Find new furthest flag in closest_flags list
            furthest_dist_closest_flags, furthest_index = furthest_flag_distance_and_index(closest_flags)
        i += 1

    return closest_flags


def _approx_position(flags: [Flag], state: PlayerState):
    if len(flags) < 2:
        # print("Less than 2 flags available")
        return

    if len(flags) > MAX_FLAGS_FOR_POSITION_ESTIMATE:
        flags = find_closest_flags(flags, MAX_FLAGS_FOR_POSITION_ESTIMATE)

    all_solutions = _find_all_solutions(flags)

    if len(all_solutions) == 2:
        # print("only two flags visible")
        solution_1_plausible = is_possible_position(all_solutions[0], state)
        solution_2_plausible = is_possible_position(all_solutions[1], state)

        if solution_1_plausible and solution_2_plausible:
            # print("both solutions match")
            return

        if solution_1_plausible:
            state.update_position(all_solutions[0], state.world_view.sim_time)
            # print(all_solutions[0])
            return
        if solution_2_plausible:
            state.update_position(all_solutions[1], state.world_view.sim_time)
            # print(all_solutions[1])
            return

        # print("no position trilaterations match previous positions")
    else:
        # handle case where this return an uncertain result
        solution = _find_mean_solution(all_solutions, state)
        if solution is not None and is_possible_position(solution, state):
            state.update_position(solution, state.now())
        else:
            pass
            # print("impossible position solution or no solution at all" + str(solution))
