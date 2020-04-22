import time
import player.player_client as client
import atexit
import signal
import subprocess

from coach.coach import Coach


def shut_down_gracefully():
    print("Shutting down...")
    for player in player_threads:
        player.stop()
        player.join()
    coach_1.stop()
    coach_1.join()
    coach_2.stop()
    coach_2.join()
    soccer_sim.send_signal(signal.SIGINT)
    soccer_monitor.send_signal(signal.SIGINT)


TEAM_NAMES = ["Team1", "Team2"]
NUM_PLAYERS = 4

player_threads = []
coach_1: Coach
coach_2: Coach

UDP_IP = "127.0.0.1"
UDP_PORT = 6000

# server::say_coach_cnt_max=-1
# server::freeform_send_period=1
# server::freeform_wait_period=0
soccer_sim = subprocess.Popen([
                                  "rcssserver server::say_coach_cnt_max=-1 server::freeform_send_period=6000 server::freeform_wait_period=-1 server::coach = false server::clang_mess_delay = 0"],
                              shell=True)
# Use soccerwindow2: soccerwindow2 --kill-server
# Use regular monitor: rcssmonitor
soccer_monitor = subprocess.Popen(["rcssmonitor"], shell=True)

# Register function to kill server, when the program is killed
atexit.register(shut_down_gracefully)

time.sleep(2)

for team in TEAM_NAMES:
    for player_num in range(NUM_PLAYERS):
        if player_num == 0:
            t = client.Client(team, UDP_PORT, UDP_IP, "goalie")
        else:
            t = client.Client(team, UDP_PORT, UDP_IP, "field")
        player_threads.append(t)
        t.start()

coach_1 = Coach(TEAM_NAMES[0], 6002, UDP_IP)
coach_1.start()

coach_2 = Coach(TEAM_NAMES[1], 6002, UDP_IP)
# coach_2.start()
