import re
import player_state

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

    print(regex_string)
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
