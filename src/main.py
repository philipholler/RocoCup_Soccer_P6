import threading
import os
import time
import player.client as player

from player.coach.coach import Coach

TEAM_NAMES = ["Team1", "Team2"]
NUM_PLAYERS = 11

player_threads = []

UDP_IP = "127.0.0.1"
UDP_PORT = 6000

# server::say_coach_cnt_max=-1
# server::freeform_send_period=1
# server::freeform_wait_period=0
soccer_sim = threading.Thread(target=lambda: os.system("rcssserver server::say_coach_cnt_max=-1 server::freeform_send_period=1 server::freeform_wait_period=0 & rcssmonitor")).start()

time.sleep(3)

for team in TEAM_NAMES:
    for player_num in range(0, NUM_PLAYERS):
        if player_num == 0:
            player.Client(team, UDP_PORT, UDP_IP, "goalie").start()
        else:
            player.Client(team, UDP_PORT, UDP_IP, "field").start()

time.sleep(2)

Coach(TEAM_NAMES[0], 6002, UDP_IP).start()

time.sleep(2)

Coach(TEAM_NAMES[1], 6002, UDP_IP).start()
