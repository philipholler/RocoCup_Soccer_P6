from math import log, exp, ceil

import numpy

from constants import QUANTIZE_STEP_OBJECTS, QUANTIZE_STEP_LANDMARKS, EPSILON

DEBUG_DICT = {
    "POSITIONAL": False,
    "ALL": False,
    "SCENARIOS": False,
    "INTERCEPTION": False,
    "KICK": False,
    "ACTIONS": False,
    "ORIENTATION": False,
    "MESSAGES": False,
    "STATUS": False,
    "MODE": False,
    "GOALIE": False,
    "PASS_TARGET": False,
    "DRIBBLE": False,
    "BALL": False,
    "HAS_BALL": False,
    "OFFSIDE": False,
    "QUANTIZATION": True
}


def debug_msg(msg: str, key: str):
    if DEBUG_DICT["ALL"]:
        print(msg)
    elif DEBUG_DICT[key]:
        print(msg)


def get_flag_quantize_range(distance):
    if distance < 0.1:
        return 0, 0

    for i, upper_bound in enumerate(inverse_quantization_table):
        if abs(distance - upper_bound) <= 0.0001:
            return inverse_quantization_table[i - 1], upper_bound

    debug_msg("Invalid quantize distance: " + str(distance), "QUANTIZATION")
    return None


def _quantize_flag(distance):
    return _quantize(exp(_quantize(log(distance + EPSILON), QUANTIZE_STEP_LANDMARKS)), 0.1)


def _create_flag_quantize_table(max_dist):
    limits = [0.0]
    dist = 0.0
    last_limit = 0.0
    step_size = 0.001
    while dist < max_dist:
        dist += step_size
        new_limit = _quantize_flag(dist)
        if new_limit > last_limit:
            last_limit = new_limit
            limits.append(new_limit)

    return limits


def _quantize(val, q):
    return numpy.rint(val / q) * q


def clamp(value, min, max):
    value = value if value > min else min
    value = value if value < max else max
    return value


inverse_quantization_table = _create_flag_quantize_table(140)

