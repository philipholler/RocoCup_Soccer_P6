import constants


def clamp(value, min, max):
    value = value if value > min else min
    value = value if value < max else max
    return value


def debug_msg(msg: str, key: str):
    if constants.DEBUG_DICT["ALL"]:
        print(msg)
    elif constants.DEBUG_DICT[key]:
        print(msg)
