"""
QUICK GUIDE:
Create a list of commands, that set up an environment for testing.
Use commands likes:
(move (ball) -47 -9.16 0 0 0)   conforming to   (move (ball) *x* *y* *direction* *delta_x* *delta_y*)
(move (player Team1 4) {0} {1} 0 0 0))   conforming to  (move (player *team* *unum*) *x* *y* *direction* *delta_x* *delta_y*)
"""



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