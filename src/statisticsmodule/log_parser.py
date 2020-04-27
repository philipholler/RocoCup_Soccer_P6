import fnmatch
import re
from pathlib import Path
import os

from statisticsmodule.statistics import Game, Team, Stage, Player
from statisticsmodule import statistics
from parsing import _ROBOCUP_MSG_REGEX, _SIGNED_INT_REGEX, _REAL_NUM_REGEX

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

    log_directory = Path(__file__).parent.parent / game.gameID
    os.makedirs(log_directory)

    file_left = open(os.path.join(log_directory, "%s_leftkicks.txt" % game.teams[0].name), "w")
    file_right = open(os.path.join(log_directory, "%s_rightkicks.txt" % game.teams[1].name), "w")
    file_l_goalie_kicks = open(os.path.join(log_directory, "%s_left_goalie_kicks.txt" % game.teams[0].name), "w")
    file_r_goalie_kicks = open(os.path.join(log_directory, "%s_right_goalie_kicks.txt" % game.teams[1].name), "w")

    files = [file_left, file_right, file_l_goalie_kicks, file_r_goalie_kicks]

    for stage in game.show_time:
        # print(game.show_time.index(stage))
        # print(stage.print_stage())
        file_left.write(str(game.show_time.index(stage)) + " " + str(stage.team_l_kicks) + "\n")
        file_right.write(str(game.show_time.index(stage)) + " " + str(stage.team_r_kicks) + "\n")
        for player in stage.players:
            if player.no == 1:
                if player.side == "l":
                    file_l_goalie_kicks.write(str(game.show_time.index(stage)) + " " + str(player.kicks) + "\n")
                if player.side == "r":
                    file_r_goalie_kicks.write(str(game.show_time.index(stage)) + " " + str(player.kicks) + "\n")

    for file in files:
        file.close()


# Gets the newest server log ".rcg"
def get_newest_server_log():
    server_log_path = os.listdir('.')
    server_log_names = fnmatch.filter(server_log_path, SERVER_LOG_PATTERN)
    server_log_names.sort(reverse=True)
    return server_log_names[0]


# Gets the newest action log ".rcl"
def get_newest_action_log():
    actions_log_path = os.listdir('.')
    action_logs = fnmatch.filter(actions_log_path, ACTION_LOG_PATTERN)
    action_logs.sort(reverse=True)
    return action_logs[0]


# Parses log name (game id, team names and goals)
def parse_log_name(log_name, game: Game):
    id_regex = "({1})\\-({0})\\_({1})\\-.*\\-({0})\\_({1})\\.".format(_ROBOCUP_MSG_REGEX, _SIGNED_INT_REGEX)
    regular_expression = re.compile(id_regex)
    matched = regular_expression.match(log_name)

    team1 = Team()
    team2 = Team()

    team1.side = "l"
    team2.side = "r"

    game.gameID = matched.group(1)
    team1.name = matched.group(2)
    team1.goals = matched.group(3)
    team2.name = matched.group(4)
    team2.goals = matched.group(5)

    game.teams.append(team1)
    game.teams.append(team2)

    print(matched.group(1))


# Parses the lines of the server log starting with "((show"
def parse_show_line(txt, game: Game):
    regex_string = "\\(show ({0}) (\\(\\([^\\)]*\\)[^\\)]*\\)) (.*)".format(_SIGNED_INT_REGEX)
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
    for player in stage.players:
        if player.side == "l" and player.kicks != 0:
            # print(str(stage.team_l_kicks) + " + " + str(player.kicks))
            stage.team_l_kicks = stage.team_l_kicks + player.kicks
            # print(str(stage.team_l_kicks))
        if player.side == "r" and player.kicks != 0:
            # print(str(stage.team_r_kicks) + " + " + str(player.kicks))
            stage.team_r_kicks = stage.team_r_kicks + player.kicks
            # print(str(stage.team_r_kicks))

    if tick <= 150:
        game.show_time.insert(tick, stage)


# Parses ball from show msg
def parse_ball(txt, stage: Stage):
    regex_string = "\\(\\(b\\) ({0}) ({0}) ({0}) ({0})".format(_REAL_NUM_REGEX)
    regular_expression = re.compile(regex_string)
    matched = regular_expression.match(txt)

    stage.ball.x_coord = float(matched.group(1))
    stage.ball.y_coord = float(matched.group(2))
    stage.ball.delta_x = float(matched.group(3))
    stage.ball.delta_y = float(matched.group(4))


# Examples:
# ((Side unum) playertype goalkeeper_bool x_coord y_coord delta_x delta_y body_angle neck_angle
# (view high narrow/normal(90)/wide) stamina (etc etc) counts ? dash turn ? move turn_neck ? ? ? ? ?
# ((l 1) 0 0x9 -50 0 0 0 35.618 -90 (v h 90) (s 8000 1 1 130300) (c 0 5 4 0 1 17 0 0 0 0 0))
# ((r 10) 0 0 30 -37 0 0 0 0 (v h 90) (s 8000 1 1 130600) (c 0 0 0 0 0 0 0 0 0 0 0))

# Parses a player from show msg
def parse_player(txt, stage: Stage):
    regex_string = "\\(\\((l|r) ({0})\\) ({0}) ({2}|0) ({1}) ({1}) ({1}) ({1}) ({1}) ({1}) \\(v [h|l] {0}\\) \\(s " \
            "{1} {1} {1} {1}\\) \\(c ({0}) ".format(_SIGNED_INT_REGEX, _REAL_NUM_REGEX, __HEX_REGEX)
    regular_expression = re.compile(regex_string)
    matched = regular_expression.match(txt)

    player = Player()
    player.side = matched.group(1)
    player.no = int(matched.group(2))
    player.x_coord = float(matched.group(5))
    player.y_coord = float(matched.group(6))
    player.kicks = int(matched.group(11))

    stage.players.append(player)
