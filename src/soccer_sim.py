import threading
import time

import player.player_client as client
import signal
import subprocess

from coaches.coach.coach import Coach
from coaches.trainer.trainer_client import Trainer
from statisticsmodule import log_parser


class SoccerSim(threading.Thread):
    def __init__(self, team_names: [str], num_players: int, trainer_mode: bool, coaches_enabled: bool, udp_player: int,
                 udp_trainer: int, udp_coach: int, udp_ip: str) -> None:
        super().__init__()
        self.team_names = team_names
        self.num_players = num_players
        self.trainer_mode = trainer_mode
        self.coaches_enabled = coaches_enabled
        self.udp_port_player = udp_player
        self.udp_port_trainer = udp_trainer
        self.udp_port_coach = udp_coach
        self.udp_ip = udp_ip

        # References for access to clients:
        self.player_threads = []
        self.coach_1: Coach = None
        self.coach_2: Coach = None
        self.trainer: Trainer = None

        # References to the simulator
        self.soccer_sim = None
        self.soccer_monitor = None

        self.has_init_clients = False

    def start(self) -> None:
        super().start()
        # server::say_coach_cnt_max=-1
        # server::freeform_send_period=1
        # server::freeform_wait_period=0
        if self.trainer_mode:
            self.soccer_sim = subprocess.Popen(["exec rcssserver server::say_coach_cnt_max=-1 server::freeform_send_period=6000 server::freeform_wait_period=-1 server::coach = true server::clang_mess_delay = 0 player::player_types = 1"],
                                                shell=True)
        else:
            self.soccer_sim = subprocess.Popen(["exec rcssserver server::say_coach_cnt_max=-1 server::freeform_send_period=6000 server::freeform_wait_period=-1 server::coach = false server::clang_mess_delay = 0 player::player_types = 1"],
                                                shell=True)

        # Use soccerwindow2: exec soccerwindow2 --kill-server --geometry=1440x900 --gradient 1 --field-grass-type lines
        # Use regular monitor: exec rcssmonitor --show-status-bar 1 --show-kick-accel-area 1 --show-catch-area 1 --geometry=1280x800
        self.soccer_monitor = subprocess.Popen(["exec rcssmonitor --show-status-bar 1 --show-kick-accel-area 1 --show-catch-area 1 --geometry=1280x800"], shell=True)


    def run(self) -> None:
        super().run()
        # Make sure the server is running before connecting players
        time.sleep(2)
        for team in self.team_names:
            for player_num in range(self.num_players):
                if player_num == 0:
                    t = client.Client(team, self.udp_port_player, self.udp_ip, "goalie")
                    t.start()
                    # Make sure, the goalie connects first to get unum 0
                    time.sleep(0.3)
                else:
                    # Everyone else get their player type from the server depending on their unum
                    t = client.Client(team, self.udp_port_player, self.udp_ip, "NaN")
                    t.start()
                self.player_threads.append(t)

        if self.trainer_mode:
            self.trainer = Trainer(self.udp_port_trainer, self.udp_ip)
            self.trainer.start()

        if self.coaches_enabled:
            self.coach_1 = Coach(self.team_names[0], self.udp_port_coach, self.udp_ip)
            self.coach_1.start()

            if len(self.team_names) > 1:
                self.coach_2 = Coach(self.team_names[1], self.udp_port_coach, self.udp_ip)
                self.coach_2.start()

        self.has_init_clients = True


    def stop(self) -> None:
        for player in self.player_threads:
            player.stop()
            player.join()

        if self.coaches_enabled:
            self.coach_1.stop()
            self.coach_1.join()
            if len(self.team_names) > 1:
                self.coach_2.stop()
                self.coach_2.join()

        if self.trainer_mode:
            self.trainer.stop()
            self.trainer.join()
        self.soccer_monitor.send_signal(signal.SIGINT)
        self.soccer_monitor.wait(3)
        self.soccer_sim.send_signal(signal.SIGINT)
        self.soccer_sim.wait(3)
        log_parser.parse_logs()