import atexit
import time

import constants
from soccer_sim import SoccerSim

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
UDP_PORT_PLAYER, UDP_PORT_TRAINER, UDP_PORT_COACH, = 6000, 6001, 6002

# Add teams and players here
team_names = ["Team1"]
num_players = 11

# Enable for more runs. Trainer is always enabled for multiple runs
MORE_SCENARIOS_MODE = False
NUM_SIMULATIONS = 3
TICKS_PER_RUN = 50

# Debugging information showed. See file constants.DEBUG_DICT to add more
constants.DEBUG_DICT["ALL"] = False

# Enable coaches
COACHES_ENABLED = True

# Enable trainer for a single run
TRAINER_SINGLE_RUN_ENABLED = False

try:
    # Run multiple games sequentially
    if MORE_SCENARIOS_MODE:
        for sim in range(NUM_SIMULATIONS):
            soccersim: SoccerSim = SoccerSim(team_names=team_names,
                                             num_players=num_players,
                                             trainer_mode=True,
                                             coaches_enabled=COACHES_ENABLED,
                                             udp_player=UDP_PORT_PLAYER,
                                             udp_trainer=UDP_PORT_TRAINER,
                                             udp_coach=UDP_PORT_COACH,
                                             udp_ip=UDP_IP)

            soccersim.start()

            # Wait for all clients to have started
            while not soccersim.has_init_clients:
                time.sleep(0.5)

            trainer = soccersim.trainer

            while trainer.think.world_view.sim_time < TICKS_PER_RUN:
                pass

            soccersim.stop()
            soccersim.join()
            print('_' * 200)
            finished_successfully = True
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
                                         udp_ip=UDP_IP)

        soccersim.start()

except KeyboardInterrupt:
    shut_down_gracefully()
