import time
import player.player_client as client
import atexit
import signal
import subprocess

from coaches.coach.coach import Coach
from coaches.trainer.trainer_client import Trainer
from statisticsmodule import log_parser


def shut_down_gracefully():
    print("Shutting down...")
    for player in player_threads:
        player.stop()
        player.join()

    if coaches_enabled:
        coach_1.stop()
        coach_1.join()
        coach_2.stop()
        coach_2.join()

    if trainer_mode:
        trainer.stop()
        trainer.join()
    soccer_monitor.send_signal(signal.SIGINT)
    soccer_monitor.wait(3)
    soccer_sim.send_signal(signal.SIGINT)
    soccer_sim.wait(3)
    log_parser.parse_logs()


TEAM_NAMES = ["Team1"]
NUM_PLAYERS = 2

trainer_mode = False
coaches_enabled = False

player_threads = []
coach_1: Coach
coach_2: Coach
trainer: Trainer

UDP_IP = "127.0.0.1"
UDP_PORT_PLAYER, UDP_PORT_TRAINER, UDP_PORT_COACH = 6000, 6001, 6002

# server::say_coach_cnt_max=-1
# server::freeform_send_period=1
# server::freeform_wait_period=0
if trainer_mode:
    soccer_sim = subprocess.Popen(["rcssserver server::say_coach_cnt_max=-1 server::freeform_send_period=6000 server::freeform_wait_period=-1 server::coach = true server::clang_mess_delay = 0 player::player_types = 1"], shell=True)
else:
    soccer_sim = subprocess.Popen(["rcssserver server::say_coach_cnt_max=-1 server::freeform_send_period=6000 server::freeform_wait_period=-1 server::coach = true server::clang_mess_delay = 0 player::player_types = 1"], shell=True)

# Use soccerwindow2: soccerwindow2 --kill-server
# Use regular monitor: rcssmonitor
soccer_monitor = subprocess.Popen(["rcssmonitor"], shell=True)

# Register function to kill server, when the program is killed
atexit.register(shut_down_gracefully)

time.sleep(2)

for team in TEAM_NAMES:
    for player_num in range(NUM_PLAYERS):
        if player_num == 0:
            t = client.Client(team, UDP_PORT_PLAYER, UDP_IP, "goalie")
            t.start()
            # Make sure, the goalie connects first to get unum 0
            time.sleep(0.3)
        else:
            # Everyone else get their player type from the server depending on their unum
            t = client.Client(team, UDP_PORT_PLAYER, UDP_IP, "NaN")
            t.start()
        player_threads.append(t)


if trainer_mode:
    trainer = Trainer(UDP_PORT_TRAINER, UDP_IP)
    trainer.start()

if coaches_enabled:
    coach_1 = Coach(TEAM_NAMES[0], UDP_PORT_COACH, UDP_IP)
    coach_1.start()

    coach_2 = Coach(TEAM_NAMES[1], UDP_PORT_COACH, UDP_IP)
    coach_2.start()