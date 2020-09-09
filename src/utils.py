from math import log, exp, ceil

import numpy

from configurations import QUANTIZE_STEP_OBJECTS, QUANTIZE_STEP_LANDMARKS, EPSILON

# When a key(category) is set to True, debugging information will be printed for anything related to that category
# Often these messages are only printed for 'test players'. To mark a test player, see the is_test_player() function
# in the player.py file
DEBUG_DICT = {
    "ALL": False,
    "POSITIONAL": False,
    "PARSING": False,
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
    "QUANTIZATION": False,
    "VELOCITY": False,
    "SENT_COMMANDS": False,
    "BIPTEST": False,
    "STAMINA_STRAT": False,
    "FREE_POSITION": False,
    "DRIBBLE_PASS_MODEL": False,
    "PASS_CHAIN": False
}


def debug_msg(msg: str, key: str):
    if DEBUG_DICT["ALL"] or DEBUG_DICT[key]:
        print(msg)


def clamp(value, lower_bound, upper_bound):
    value = value if value > lower_bound else lower_bound
    value = value if value < upper_bound else upper_bound
    return value


"""
The following functions are used to inverse 
the quantization that the robocup server applies to the
sensory data. 
The inverse quantization provides the possible 
range of values that could have produced the given value.  
For example values in the range 21-29 might always be quantized to the value 24.6
"""


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


inverse_quantization_table = _create_flag_quantize_table(140)

