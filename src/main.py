import atexit
import time

import constants
from player.player_client import Client
from soccer_sim import SoccerSim

def shut_down_gracefully() -> None:
    soccersim.stop()

UDP_IP = "127.0.0.1"
UDP_PORT_PLAYER, UDP_PORT_TRAINER, UDP_PORT_COACH = 6000, 6001, 6002

team_names = ["Team1"]

NUM_SIMULATIONS = 2
NUM_TICKS = 20

constants.DEBUG_MODE_ALL = False
constants.


DEBUG_MODE_POSITIONAL, DEBUG_MODE_ALL, DEBUG_MODE_SCENARIOS = False, False, False

for sim in range(NUM_SIMULATIONS):
    soccersim: SoccerSim = SoccerSim(team_names=team_names,
                                     num_players=2,
                                     trainer_mode=False,
                                     coaches_enabled=False,
                                     udp_player=UDP_PORT_PLAYER,
                                     udp_trainer=UDP_PORT_TRAINER,
                                     udp_coach=UDP_PORT_COACH,
                                     udp_ip=UDP_IP)

    # Register function to kill server, when the program is killed
    atexit.register(shut_down_gracefully)

    soccersim.start()

    first_player: Client = soccersim.player_threads[0]
    while first_player.think.player_state.world_view.sim_time < NUM_TICKS:
        print("First_player time: ", first_player.think.player_state.world_view.sim_time)
        time.sleep(0.001)

    print('_'*20)
    soccersim.stop()
    soccersim.join()







