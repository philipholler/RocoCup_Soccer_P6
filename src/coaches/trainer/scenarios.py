"""
QUICK GUIDE:
Create a list of commands, that set up an environment for testing.
Use commands likes:
(move (ball) -47 -9.16 0 0 0)   conforming to   (move (ball) *x* *y* *direction* *delta_x* *delta_y*)
(move (player Team1 4) {0} {1} 0 0 0))   conforming to  (move (player *team* *unum*) *x* *y* *direction* *delta_x* *delta_y*)
"""
import random

from coaches.world_objects_coach import WorldViewCoach, PlayerViewCoach, BallOnlineCoach
from configurations import TEAM_2_NAME, TEAM_1_NAME
from geometry import Coordinate
from uppaal.strategy import generate_strategy

'''
Fitting the following positions for passing strat optimization:
_player_positions = [(6, 10), (10, 22), (26, 18), (32, 18), (26, 12)]
_opponent_positions = [(16, 20), (28, 18), (25, 0), (28, 18), (14, 22)]
'''
passing_strat = [
    "(move (ball) 6.3 10.3)",
    "(move (player Team1 1) 6 10))",
    "(move (player Team1 2) 10 22))",
    "(move (player Team1 3) 26 18))",
    "(move (player Team1 4) 32 18))",
    "(move (player Team1 5) 26 12))",
    "(move (player Team2 1) 16 20))",
    "(move (player Team2 2) 28 18))",
    "(move (player Team2 3) 25 0))",
    "(move (player Team2 4) 28 18))",
    "(move (player Team2 5) 14 22))"
]


def generate_commands_coachmsg_goalie_positioning(random_seed: int, wv: WorldViewCoach):
    # Set seed for random generator
    random.seed(random_seed)

    # Generate player position
    striker_x_pos = 36.5
    striker_y_pos = random.randint(-20, 20)
    striker = ("Team1", 2, striker_x_pos, striker_y_pos)

    goalie_x_pos = 50
    goalie_y_pos = 0
    goalie = ("Team2", 1, goalie_x_pos, goalie_y_pos)

    ball_x_pos = striker_x_pos + 0.4
    ball_y_pos = striker_y_pos
    ball = (ball_x_pos, ball_y_pos)

    commands = _generate_commands([striker, goalie], ball)

    should_dribble = bool(random.getrandbits(1))
    if should_dribble:
        # If standing high, always dribble down
        if striker_y_pos > 10:
            direction = random.randint(270, 360)
        # If standing low, always dribble up
        elif striker_y_pos < -10:
            direction = random.randint(0, 90)
        # Else dribble randomly
        else:
            if bool(random.getrandbits(1)):
                direction = random.randint(270, 360)
            else:
                direction = random.randint(0, 90)

    striker_target_y = random.randint(-5, 5)

    if should_dribble:
        return commands, ["(dribble {0})".format(direction), "(striker_target_y {0})".format(striker_target_y)]
    else:
        return commands, ["(striker_target_y {0})".format(striker_target_y)]


def generate_commands_coachmsg_passing_strat(random_seed: int, wv: WorldViewCoach):
    """
    :param random_seed:
    :return: 1: list of commands to move objects into scenario, 2: say msg for coach
    """
    # Set seed for random generator
    random.seed(random_seed)
    players: [] = _generate_players_passing_strat()
    ball_pos = (float(players[0][2]) + 0.5, float(players[0][3]))
    _update_world_view_passing_strat(wv, players, ball_pos)
    passing_strat_commands: [] = _generate_commands(players, ball_pos)
    coach_msg = generate_strategy(wv)

    return passing_strat_commands, coach_msg

def _generate_players_passing_strat() -> []:
    """
    :return: List of players as tuple. (team, unum, x_pos, y_pos)
    """
    players: [] = []
    possessor = None
    for team in [TEAM_1_NAME, TEAM_2_NAME]:
        for player in range(2, 7):
            # Generate possessor
            if team == TEAM_1_NAME and player == 2:
                unum: int = player
                x_pos = random.randint(-45, -40)
                y_pos = random.randint(-15, 15)
                players.append((team, unum, x_pos, y_pos))
                possessor = (team, unum, x_pos, y_pos)
            # Generate other players
            else:
                unum: int = player
                # Position should not be closer than 10 meters
                x_pos = random.randint(possessor[2] + 10, possessor[2] + 35)
                y_pos = random.randint(possessor[3] - 20, possessor[3] + 20)
                players.append((team, unum, x_pos, y_pos))

    return players

def _update_world_view_passing_strat(wv: WorldViewCoach, players, ball_pos):
    # Players -> List of players as tuple. (team, unum, x_pos, y_pos)
    # Add all players to world view
    for player in players:
        if player[0] == TEAM_1_NAME and player[1] == 2:
            new_player: PlayerViewCoach = PlayerViewCoach(player[0], player[1], False, Coordinate(player[2], player[3])
                                                          , 0, 0, 0, 0, True)
        else:
            new_player: PlayerViewCoach = PlayerViewCoach(player[0], player[1], False, Coordinate(player[2], player[3])
                                                          , 0, 0, 0, 0, False)
        wv.players.append(new_player)


    # Add ball to world view
    ball: BallOnlineCoach = BallOnlineCoach(Coordinate(ball_pos[0], ball_pos[1]), 0, 0)
    wv.ball = ball

def _generate_commands(players, ball_pos):
    """
    :param players: List of players as tuple. (team, unum, x_pos, y_pos)
    :param ball_pos: Tuple as such (x_pos, y_pos)
    :return:
    """
    commands = []
    # Move all players
    for player in players:
        commands.append("(move (player {0} {1}) {2} {3}))".format(player[0], player[1], player[2], player[3]))

    # Move ball to position
    commands.append("(move (ball) {0} {1} 0 0 0)".format(ball_pos[0], ball_pos[1]))

    return commands