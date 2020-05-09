
DEBUG_DICT = {
    "POSITIONAL": False,
    "ALL": False,
    "SCENARIOS": False,
    "INTERCEPTION": False,
    "KICK": False,
    "ACTIONS": False,
    "ORIENTATION": False,
    "MESSAGES": True,
    "STATUS": False,
    "MODE": False,
    "GOALIE": False,
    "PASS_TARGET": False,
    "DRIBBLE": False,
    "BALL": False,
    "HAS_BALL": False,
    "OFFSIDE": False
}


def clamp(value, min, max):
    value = value if value > min else min
    value = value if value < max else max
    return value


def debug_msg(msg: str, key: str):
    if DEBUG_DICT["ALL"]:
        print(msg)
    elif DEBUG_DICT[key]:
        print(msg)