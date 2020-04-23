import fnmatch
import re
from pathlib import Path

from statisticsmodule import SERVER_LOG_PATH, ACTIONS_LOG_PATH
from statisticsmodule.statistics import Game, Team, Stage, Player
from statisticsmodule import statistics
from parsing import __ROBOCUP_MSG_REGEX, __SIGNED_INT_REGEX, __REAL_NUM_REGEX

SERVER_LOG_PATTERN = '*.rcg'
ACTION_LOG_PATTERN = '*.rcl'
__HEX_REGEX = "0[xX][0-9a-fA-F]+"


# Main method
def parse_logs():
    game = statistics.Game()
    log_name = get_newest_server_log()
    parse_log_name(log_name, game)

    file = open(Path(__file__).parent.parent / log_name, 'r')

    for line in file:
        if line.startswith("(show "):
            parse_show_line(line, game)
        else:
            continue


# Gets the newest server log ".rcg"
def get_newest_server_log():
    server_log_names = fnmatch.filter(SERVER_LOG_PATH, SERVER_LOG_PATTERN)
    server_log_names.sort(reverse=True)
    return server_log_names[0]


# Gets the newest action log ".rcl"
def get_newest_action_log():
    action_logs = fnmatch.filter(ACTIONS_LOG_PATH, ACTION_LOG_PATTERN)
    action_logs.sort(reverse=True)
    return action_logs[0]


# Parses log name (game id, team names and goals)
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


# Parses the lines of the server log starting with "((show"
def parse_show_line(txt, game: Game):
    regex_string = "\\(show ({0}) (\\(\\([^\\)]*\\)[^\\)]*\\)) (.*)".format(__SIGNED_INT_REGEX)
    regular_expression = re.compile(regex_string)
    matched = regular_expression.match(txt)

    stage = Stage()
    tick = int(matched.group(1))

    ball_txt = matched.group(2)
    parse_ball(ball_txt, stage)

    players = re.findall(r'\(\([^)]*\)[^)]*\)[^)]*\)[^)]*\)', matched.group(3))
    for player in players:
        parse_player(player, stage)

    # Inserts the stage in the correct array slot (tick)
    game.show_time.insert(tick, stage)


# Parses ball from show msg
def parse_ball(txt, stage: Stage):
    regex_string = "\\(\\(b\\) ({0}) ({0}) ({0}) ({0})".format(__REAL_NUM_REGEX)
    regular_expression = re.compile(regex_string)
    matched = regular_expression.match(txt)

    stage.ball.x_coord = float(matched.group(1))
    stage.ball.y_coord = float(matched.group(2))
    stage.ball.delta_x = float(matched.group(3))
    stage.ball.delta_y = float(matched.group(4))


# Examples:
# ((l 1) 0 0x9 -50 0 0 0 35.618 -90 (v h 90) (s 8000 1 1 130300) (c 0 5 4 0 1 17 0 0 0 0 0))
# ((r 10) 0 0 30 -37 0 0 0 0 (v h 90) (s 8000 1 1 130600) (c 0 0 0 0 0 0 0 0 0 0 0))

# Parses a player from show msg TODO: find out what rest of string means
def parse_player(txt, stage: Stage):
    regex_string = "\\(\\((l|r) ({0})\\) ({0}) ({2}|0) ({1}) ({1})".format(__SIGNED_INT_REGEX, __REAL_NUM_REGEX,
                                                                           __HEX_REGEX)
    regular_expression = re.compile(regex_string)
    matched = regular_expression.match(txt)

    player = Player()
    player.side = matched.group(1)
    player.no = int(matched.group(2))
    player.x_coord = float(matched.group(5))
    player.y_coord = float(matched.group(6))

    stage.players.append(player)
