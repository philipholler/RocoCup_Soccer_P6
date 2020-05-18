import atexit
import os
import random
import time
from pathlib import Path

from coaches.trainer import scenarios
from coaches.world_objects_coach import WorldViewCoach
from fake_monitor.fake_monitor_thread import FakeMonitorClient
from soccer_sim import SoccerSim
from utils import DEBUG_DICT

finished_successfully = False
soccersim: SoccerSim


def shut_down_gracefully() -> None:
    if finished_successfully:
        pass
    else:
        soccersim.stop()
        soccersim.join()
    exit(0)

# Network settings
UDP_IP = "127.0.0.1"
UDP_PORT_PLAYER, UDP_PORT_TRAINER, UDP_PORT_COACH, UDP_PORT_MONITOR = 6000, 6001, 6002, 6000

# Add teams and players here
team_names = ["Team1", "Team2"]
num_players = 11

# Enable monitor
monitor_enabled = True

# Enable for more runs. Trainer is always enabled for multiple runs
MORE_SCENARIOS_TRAINER_MODE = False
NUM_SIMULATIONS = 100
TICKS_PER_RUN = 100

# Run more games sequentially to test game performance
MORE_GAMES_WITH_FAKE_MONITOR_MODE = True
NUM_GAMES = 5

# Debugging information showed. See file constants.DEBUG_DICT to add more
DEBUG_DICT["ALL"] = False

# Enable coaches
COACHES_ENABLED = True

# Enable trainer for a single run
TRAINER_SINGLE_RUN_ENABLED = False

# Logparser stuffs
stat_dir = Path(__file__).parent / "Statistics"
if not stat_dir.exists():
    os.makedirs(stat_dir)
game_number_path = stat_dir / "game_number.txt"
game_number = 1

try:
    # Run multiple games sequentially
    if MORE_SCENARIOS_TRAINER_MODE:
        random.seed(123456237890)
        for sim in range(NUM_SIMULATIONS):
            # Generate passing strat
            """commands, coach_msg = scenarios.generate_commands_coachmsg_passing_strat(random.randint(0, 1000000000),
                                                                                     wv=WorldViewCoach(0, "Team1"))"""

            # For coach positioning strategy
            commands, coach_msgs = scenarios.generate_commands_coachmsg_goalie_positioning(random.randint(0, 1000000000),
                                                                                          wv=WorldViewCoach(0, "Team1"))

            soccersim: SoccerSim = SoccerSim(team_names=team_names,
                                             num_players=num_players,
                                             trainer_mode=True,
                                             coaches_enabled=COACHES_ENABLED,
                                             udp_player=UDP_PORT_PLAYER,
                                             udp_trainer=UDP_PORT_TRAINER,
                                             udp_coach=UDP_PORT_COACH,
                                             udp_ip=UDP_IP,
                                             enable_monitor=monitor_enabled)

            soccersim.start()

            # Wait for all clients to have started
            while not soccersim.has_init_clients:
                time.sleep(0.5)

            # Make trainer say commands to move players around
            for command in commands:
                print("Trainer sending: ", command)
                soccersim.trainer.think.say_command(command)


            # Give commands from coach
            print("Coach sending: ", coach_msgs)
            for msg in coach_msgs:
                soccersim.coach_1.think.say(msg)

            trainer = soccersim.trainer

            # Start game
            trainer.think.change_game_mode("play_on")

            while trainer.think.world_view.sim_time < TICKS_PER_RUN:
                pass

            try:
                with open(game_number_path, "w") as file:
                    print(str(game_number_path))
                    file.write(str(game_number))
                    game_number += 1
            except Exception:
                print("Log parser failed")

            soccersim.stop()
            soccersim.join()
            print("Done with run {0} of {1}".format(sim + 1, NUM_SIMULATIONS))
            print('_' * 200)
            finished_successfully = True
    elif MORE_GAMES_WITH_FAKE_MONITOR_MODE:
        atexit.register(shut_down_gracefully)
        for game in range(NUM_GAMES):
            soccersim: SoccerSim = SoccerSim(team_names=team_names,
                                             num_players=num_players,
                                             trainer_mode=TRAINER_SINGLE_RUN_ENABLED,
                                             coaches_enabled=COACHES_ENABLED,
                                             udp_player=UDP_PORT_PLAYER,
                                             udp_trainer=UDP_PORT_TRAINER,
                                             udp_coach=UDP_PORT_COACH,
                                             udp_ip=UDP_IP,
                                             enable_monitor=False)

            soccersim.start()
            time.sleep(2)
            fake_monitor = FakeMonitorClient(start_time=5, UDP_IP=UDP_IP, UDP_PORT=UDP_PORT_MONITOR)
            fake_monitor.start()

            try:
                with open(game_number_path, "w") as file:
                    print(str(game_number_path))
                    file.write(str(game_number))
                    game_number += 1
            except Exception:
                print("Log parser failed")

            while fake_monitor.thinker.current_tick < 100:
                time.sleep(0.1)

            soccersim.stop()
            soccersim.join()
            fake_monitor.stop()
            fake_monitor.join()
    # Run a single game
    else:
        atexit.register(shut_down_gracefully)
        soccersim: SoccerSim = SoccerSim(team_names=team_names,
                                         num_players=num_players,
                                         trainer_mode=TRAINER_SINGLE_RUN_ENABLED,
                                         coaches_enabled=COACHES_ENABLED,
                                         udp_player=UDP_PORT_PLAYER,
                                         udp_trainer=UDP_PORT_TRAINER,
                                         udp_coach=UDP_PORT_COACH,
                                         udp_ip=UDP_IP,
                                         enable_monitor=monitor_enabled)

        soccersim.start()

        try:
            with open(game_number_path, "w") as file:
                print(str(game_number_path))
                file.write(str(game_number))
                game_number += 1
        except Exception:
            print("Log parser failed")


except KeyboardInterrupt:
    shut_down_gracefully()
