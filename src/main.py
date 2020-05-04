import atexit
import time

import constants
from player.player_client import Client
from soccer_sim import SoccerSim
from utils import debug_msg


def shut_down_gracefully() -> None:
    soccersim.stop()
    soccersim.join()


UDP_IP = "127.0.0.1"
UDP_PORT_PLAYER, UDP_PORT_TRAINER, UDP_PORT_COACH, = 6000, 6001, 6002

team_names = ["Team1", "Team2"]
num_players = 5

# Enable for more runs
MORE_SCENARIOS_MODE = True
NUM_SIMULATIONS = 3
TICKS_PER_RUN = 50

constants.DEBUG_DICT["ALL"] = False

COACHES_ENABLED = True

# Register function to kill server, when the program is killed
atexit.register(shut_down_gracefully)

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
            time.sleep(0.1)

        soccersim.stop()
        soccersim.join()
        print('_' * 200)

# Run a single game
else:
    soccersim: SoccerSim = SoccerSim(team_names=team_names,
                                     num_players=num_players,
                                     trainer_mode=False,
                                     coaches_enabled=COACHES_ENABLED,
                                     udp_player=UDP_PORT_PLAYER,
                                     udp_trainer=UDP_PORT_TRAINER,
                                     udp_coach=UDP_PORT_COACH,
                                     udp_ip=UDP_IP)
    soccersim.start()
