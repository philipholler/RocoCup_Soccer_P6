
DEBUG_DICT = {
    "POSITIONAL": False,
    "ALL": False,
    "SCENARIOS": False,
    "INTERCEPTION": True,
    "KICK": False,
    "ACTIONS": False,
    "ORIENTATION": False,
    "MESSAGES": False,
    "STATUS": True,
    "MODE": False,
    "GOALIE": False,
    "DRIBBLE": True,
    "BALL": True
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
4