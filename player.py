import time

import player_state
import player_connection
import parsing
import thinker


class Player:

    # Start up the player
    def __init__(self, team: str, UDP_PORT, UDP_IP) -> None:
        # Init thinker thread
        self.think = thinker.Thinker(team)
        # Init player connection thread
        self.player_conn = player_connection.PlayerConnection(UDP_PORT=UDP_PORT, UDP_IP=UDP_IP, think=self.think)
        # Give reference of connection to thinker thread
        self.think.player_conn = self.player_conn

        # Connect to server with team name from thinker
        self.player_conn.start()
        # Start thinking
        self.think.start()
