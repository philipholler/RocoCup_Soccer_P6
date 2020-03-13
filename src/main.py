import threading
import os
import time
import player.client as player

TEAM_NAMES = ["Team1", "Team2"]
NUM_PLAYERS = 11

player_threads = []

UDP_IP = "127.0.0.1"
UDP_PORT = 6000

soccer_sim = threading.Thread(target=lambda: os.system("rcsoccersim")).start()

time.sleep(3)

for team in TEAM_NAMES:
    for player_num in range(0, NUM_PLAYERS):
        player.Client(team, UDP_PORT, UDP_IP).start()