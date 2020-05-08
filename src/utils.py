from math import log, exp, ceil

from constants import QUANTIZE_STEP_OBJECTS

DEBUG_DICT = {
    "POSITIONAL": True,
    "ALL": False,
    "SCENARIOS": False,
    "INTERCEPTION": False,
    "KICK": False,
    "ACTIONS": True,
    "ORIENTATION": True,
    "MESSAGES": False,
    "STATUS": True,
    "MODE": False,
    "GOALIE": False,
    "BALL": True,
    "PASS_TARGET": False,
    "DRIBBLE": False,
    "HAS_BALL": False
}


def debug_msg(msg: str, key: str):
    if DEBUG_DICT["ALL"]:
        print(msg)
    elif DEBUG_DICT[key]:
        print(msg)


def get_quantize_range(distance):
    if distance == 0:
        return 0, 0

    for i, upper_bound in enumerate(inverse_quantization_table):
        if distance < upper_bound:
            return inverse_quantization_table[i - 1], upper_bound


def _quantize_objects(distance):
    return _quantize(exp(_quantize(log(distance))))


def _create_quantize_table(max_dist):
    limits = [0.0]
    dist = 0.0
    last_limit = 0.0
    while dist < max_dist:
        dist += 0.02
        new_limit = _quantize_objects(dist)
        if new_limit > last_limit:
            last_limit = new_limit
            limits.append(new_limit)

    return limits


def _quantize(val):
    return ceil(val / QUANTIZE_STEP_OBJECTS) * QUANTIZE_STEP_OBJECTS


def clamp(value, min, max):
    value = value if value > min else min
    value = value if value < max else max
    return value


inverse_quantization_table = _create_quantize_table(140)
