import math
import re
from player import player_state
from math import sqrt, atan2

REAL_NUM_REGEX = "[0-9]*.?[0-9]*"
SIGNED_INT_REGEX = "[-0-9]*"
ROBOCUP_MSG_REGEX = "[-0-9a-zA-Z ().+*/?<>_]*"


def parse_message_update_state(msg: str, ps: player_state):
    if msg.startswith("(hear"):
        __parse_hear(msg, ps)
    elif msg.startswith("(sense_body"):
        __parse_body_sense(msg, ps)
    elif msg.startswith("(init"):
        __parse_init(msg, ps)


def __parse_init(msg, ps: player_state.PlayerState):
    regex = re.compile("\\(init ([lr]) ([0-9]*)")
    matched = regex.match(msg.__str__())
    ps.side = matched.group(1)
    ps.player_num = matched.group(2)


# Three different modes
# example: (hear 0 referee kick_off_l)
# example: (hear 0 self *msg*)
# Pattern: (hear *time* *degrees* *msg*)
def __parse_hear(text: str, ps: player_state):
    split_by_whitespaces = re.split('\\s+', text)
    time = split_by_whitespaces[1]
    ps.sim_time = time  # Update players understanding of time

    sender = split_by_whitespaces[2]
    if sender == "referee":
        regex_string = "\\(hear ({0}) referee ({1})\\)".format(SIGNED_INT_REGEX, ROBOCUP_MSG_REGEX)

        regular_expression = re.compile(regex_string)
        matched = regular_expression.match(text)

        ps.game_state = matched.group(2)

        return
    elif sender == "self":
        return
    else:
        regex_string = "\\(hear ({0}) ({0}) ({1})\\)".format(SIGNED_INT_REGEX, ROBOCUP_MSG_REGEX)

        regular_expression = re.compile(regex_string)
        matched = regular_expression.match(text)

        return


# example : (sense_body 0 (view_mode high normal) (stamina 8000 1) (speed 0) (kick 0) (dash 0) (turn 0) (say 0))
# Group [1] = time, [2] = stamina, [3] = effort, [4] = speed, [5] = kick count, [6] = dash, [7] = turn
def __parse_body_sense(text: str, ps: player_state):
    # Will view_mode ever change from "high normal"?
    regex_string = ".*sense_body ({1}).*stamina ({0}) ({0})\\).*speed ({0})\\).*kick ({0})\\)"
    regex_string += ".*dash ({0})\\).*turn ({1})\\)"
    regex_string = regex_string.format(REAL_NUM_REGEX, SIGNED_INT_REGEX)

    regular_expression = re.compile(regex_string)
    matched = regular_expression.match(text)

    return matched


# Example : (see 0 ((flag r b) 48.9 29) ((flag g r b) 42.5 -4) ((goal r) 43.8 -13) ((flag g r t) 45.6 -21)
#           ((flag p r b) 27.9 21) ((flag p r c) 27.9 -21 0 0) ((Player) 1 -179) ((player Team2 2) 1 0 0 0)
#           ((Player) 0.5 151) ((player Team2 4) 0.5 -28 0 0) ((line r) 42.5 90))
def __parse_flags(text):
    flag_regex = "\\(flag [^)]*\\) {0} {0}".format(REAL_NUM_REGEX)
    return re.findall(flag_regex, text)


def __parse_players(text):
    flag_regex = " [^)]*".format(REAL_NUM_REGEX, SIGNED_INT_REGEX)
    return re.findall(flag_regex, text)


def __match(regex_string, text):
    regular_expression = re.compile(regex_string)
    regex_match = regular_expression.match(text)
    return regex_match


def __flag_position(pos_x, pos_y):
    return None


# for m in reg_str.groups():
#    print(m)


FLAG_COORDS = {
    # perimiter flags
    "tl50": (-50, 40),
    "tl40": (-40, 40),
    "tl30": (-30, 40),
    "tl20": (-20, 40),
    "tl10": (-10, 40),
    "t0": (0, 40),
    "tr10": (10, 40),
    "tr20": (20, 40),
    "tr30": (30, 40),
    "tr40": (40, 40),
    "tr50": (50, 40),

    "rt30": (60, 30),
    "rt20": (60, 20),
    "rt10": (60, 10),
    "r0": (60, 0),
    "rb10": (60, -10),
    "rb20": (60, -20),
    "rb30": (60, -30),

    "bl50": (-50, -40),
    "bl40": (-40, -40),
    "bl30": (-30, -40),
    "bl20": (-20, -40),
    "bl10": (-10, -40),
    "b0": (0, -40),
    "br10": (10, -40),
    "br20": (20, -40),
    "br30": (30, -40),
    "br40": (40, -40),
    "br50": (50, -40),

    "lt30": (-60, 30),
    "lt20": (-60, 20),
    "lt10": (-60, 10),
    "l0": (-60, 0),
    "lb10": (-60, -10),
    "lb20": (-60, -20),
    "lb30": (-60, -30),

    # goal flags ('t' and 'b' flags can change based on server parameter
    # 'goal_width', but we leave their coords as the default values.
    "glt": (-55, 7.01),
    "gl": (-55, 0),
    "glb": (-55, -7.01),

    "grt": (55, 7.01),
    "gr": (55, 0),
    "grb": (55, -7.01),

    # penalty flags
    "plt": (-35, 20),
    "plc": (-35, 0),
    "plb": (-32, -20),

    "prt": (35, 20),
    "prc": (35, 0),
    "prb": (32, -20),

    # field boundary flags (on boundary lines)
    "lt": (-55, 35),
    "ct": (0, 35),
    "rt": (55, 35),

    "lb": (-55, -35),
    "cb": (0, -35),
    "rb": (55, -35),

    # center flag
    "c": (0, 0)
}


# example : (sense_body 0 (view_mode high normal) (stamina 8000 1) (speed 0) (kick 0) (dash 0) (turn 0) (say 0))
# Group [1] = time, [2] = stamina, [3] = effort, [4] = speed, [5] = kick count, [6] = dash, [7] = turn
def parse_body_sense(text):
    # Will view_mode ever change from "high normal"?
    regex_string = ".*sense_body ({1}).*stamina ({0}) ({0})\\).*speed ({0})\\).*kick ({0})\\)"
    regex_string += ".*dash ({0})\\).*turn ({1})\\)".format(REAL_NUM_REGEX, SIGNED_INT_REGEX)
    regex_string = regex_string.format(REAL_NUM_REGEX, SIGNED_INT_REGEX)

    regular_expression = re.compile(regex_string)
    matched = regular_expression.match(text)

    return matched


# Example : (see 0 ((flag r b) 48.9 29) ((flag g r b) 42.5 -4) ((goal r) 43.8 -13) ((flag g r t) 45.6 -21)
#           ((flag p r b) 27.9 21) ((flag p r c) 27.9 -21 0 0) ((Player) 1 -179) ((player Team2 2) 1 0 0 0)
#           ((Player) 0.5 151) ((player Team2 4) 0.5 -28 0 0) ((line r) 42.5 90))
def parse_flags(text):
    flag_regex = "\\(flag [^\\)]*\\) {0} {0}".format(REAL_NUM_REGEX)
    return re.findall(flag_regex, text)


def parse_goal(text):
    # todo
    flag_regex = "\\(flag [^\\)]*\\) {0} {0}".format(REAL_NUM_REGEX)
    return re.findall(flag_regex, text)


def parse_players(text):
    flag_regex = "\\(\\(".format(REAL_NUM_REGEX, SIGNED_INT_REGEX)
    return re.findall(flag_regex, text)


def match(regex_string, text):
    regular_expression = re.compile(regex_string)
    regex_match = regular_expression.match(text)
    return regex_match


def extract_flag_identifiers(flags):
    flag_identifiers_regex = ".*\\(flag ([^\\)]*)\\)"
    flag_identifiers = []
    for flag in flags:
        m = match(flag_identifiers_regex, flag)
        flag_identifiers.append(m.group(1).replace(" ", ""))
    return flag_identifiers


def extract_flag_distances(flags):
    flag_distance_regex = ".*\\(flag [^\\)]*\\) ({0})".format(REAL_NUM_REGEX)
    flag_identifiers = []
    for flag in flags:
        m = match(flag_distance_regex, flag)
        flag_identifiers.append(m.group(1).replace(" ", ""))
    return flag_identifiers


def extract_flag_coordinates(flag_ids):
    coords = []
    for flag_id in flag_ids:
        coords.append(FLAG_COORDS.get(flag_id))
    return coords


def zip_flag_coords_distance(flags):
    coords_zipped_distance = []
    flag_ids = extract_flag_identifiers(flags)
    flag_coords = extract_flag_coordinates(flag_ids)
    flag_distances = extract_flag_distances(flags)

    for i in range(0, flag_ids.__len__()):
        coords_zipped_distance.append((flag_coords.__getitem__(i), flag_distances.__getitem__(i)))

    return coords_zipped_distance


def calculate_distance(coord1, coord2):
    x_dist = abs(coord1[0] - coord2[0])
    y_dist = abs(coord1[1] - coord2[1])
    return sqrt(pow(float(x_dist), 2) + pow(float(y_dist), 2))


def trilaterate_offset(flag_one, flag_two):
    coord1 = flag_one[0]
    coord2 = flag_two[0]
    distance_between_flags = calculate_distance(coord1, coord2)
    distance_to_flag1 = float(flag_one[1])
    distance_to_flag2 = float(flag_two[1])
    x = (distance_to_flag1 - distance_to_flag2) / (2.0 * distance_between_flags)
    y = sqrt(distance_to_flag1 - pow(x, 2.0))
    return x, y


def calculate_angle_between(coordinate1, coordinate2):
    return atan2(coordinate1[0] - coordinate2[0], coordinate1[1] - coordinate2[1])


def rotate_coordinate(coord, radians_to_rotate):
    new_x = math.cos(radians_to_rotate) * coord[0] - math.sin(radians_to_rotate) * coord[1]
    new_y = math.sin(radians_to_rotate) * coord[0] + math.cos(radians_to_rotate) * coord[1]
    return new_x, new_y


def approximate_position(coords_and_distance):
    flag_one = coords_and_distance.__getitem__(0)
    flag_two = coords_and_distance.__getitem__(1)
    unrotated_offset_from_flag_one = trilaterate_offset(flag_one, flag_two)
    radians_to_rotate = calculate_angle_between((1, 0), flag_two[0])
    corrected_offset_from_flag_one = rotate_coordinate(unrotated_offset_from_flag_one, radians_to_rotate)



parsed_flags = parse_flags(
    "(see 0 ((flag r b) 48.9 29) ((flag g r b) 42.5 -4) ((goal r) 43.8 -13) ((flag g r t) 45.6 -21) ("
    "(flag p r b) 27.9 21) ((flag p r c) 27.9 -21 0 0) ((Player) 1 -179) ((player Team2 2) 1 0 0 0) ("
    "(Player) 0.5 151) ((player Team2 4) 0.5 -28 0 0) ((line r) 42.5 90))")
approximate_position(zip_flag_coords_distance(parsed_flags))


'''
- Returns the position of an object.
object_rel_angle is the relative angle to the observer (-180 to 180)
distance is the distance from the observer to the object
my_x, my_y are the coordinates of the observer
my_angle is the global angle of the observer

example: 
My pos: x: -19,  y: -16 my_angle 0
(player Team1 9) 14.9 -7 0 0) = x:-4, y:-17,5
'''
def get_object_position(object_rel_angle, distance, my_x, my_y, my_angle):
    actual_angle = my_angle + object_rel_angle
    x = distance * math.cos(math.radians(actual_angle)) + my_x
    y = distance * math.sin(math.radians(actual_angle)) + my_y
    return x, y