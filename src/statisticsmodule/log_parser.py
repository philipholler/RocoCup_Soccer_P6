import fnmatch
import re
from pathlib import Path

from statisticsmodule import SERVER_LOG_PATH, ACTIONS_LOG_PATH
from statisticsmodule.statistics import Game, Team
from statisticsmodule import statistics
from parsing import __ROBOCUP_MSG_REGEX, __SIGNED_INT_REGEX

SERVER_LOG_PATTERN = '*.rcg'
ACTION_LOG_PATTERN = '*.rcl'


def parse_logs():
    game = statistics.Game()
    parse_log_name(get_newest_server_log(), game)
    log_name = str(get_newest_server_log())

    file = open(Path(__file__).parent.parent / log_name, 'r')

    for line in file:
        if line.startswith("(show "):
            parse_line(line, game)
        else:
            continue



def get_newest_server_log():
    server_log_names = fnmatch.filter(SERVER_LOG_PATH, SERVER_LOG_PATTERN)
    server_log_names.sort(reverse=True)
    return server_log_names[0]


def get_newest_action_log():
    action_logs = fnmatch.filter(ACTIONS_LOG_PATH, ACTION_LOG_PATTERN)
    action_logs.sort(reverse=True)
    return action_logs[0]


def parse_log_name(log_name, game: Game):
    id_regex = "({1})\\-({0})\\_({1})\\-.*\\-({0})\\_({1})\\.".format(__ROBOCUP_MSG_REGEX, __SIGNED_INT_REGEX)
    regular_expression = re.compile(id_regex)
    matched = regular_expression.match(log_name)

    team1 = Team()
    team2 = Team()

    game.gameID = matched.group(1)
    team1.name = matched.group(2)
    team1.goals = matched.group(3)
    team2.name = matched.group(4)
    team2.goals = matched.group(5)

    game.teams.append(team1)
    game.teams.append(team2)

    print(game.gameID)

def parse_line(txt, game: Game):

    regex_string = "\\(show ({0}) (\\(\\(.*\\)\\)) ".format(__SIGNED_INT_REGEX)
    regular_expression = re.compile(regex_string)
    matched = regular_expression.match(txt)
    print(matched.groups())