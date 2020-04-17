import functools
import re
from coach.world_objects_coach import WorldViewCoach, PlayerViewCoach, BallOnlineCoach

from uppaal.uppaal_model import UppaalModel, UppaalStrategy, execute_verifyta, Regressor

from player.world_objects import Coordinate

SYSTEM_PLAYER_NAMES = ["player0", "player1", "player2", "player3", "player4"]
PLAYER_POS_DECL_NAME = "player_pos[team_members][2]"
OPPONENT_POS_DECL_NAME = "opponent_pos[opponents][2]"


class StrategyGenerator:

    def __init__(self, strategy_name, model_modifier, strategy_parser) -> None:
        super().__init__()
        self.strategy_name = strategy_name
        self.strategy_parser = strategy_parser
        self.model_modifier = model_modifier


def generate_strategy(wv: WorldViewCoach):
    strategy_generator = find_applicable_strat(wv)
    if strategy_generator is None:
        return

    # Create model
    model = UppaalModel(strategy_generator)

    # Update model data in accordance with chosen strategy
    model_team_members = _update_passing_model(wv, model)
    execute_verifyta(model)

    uppaal_strategy = UppaalStrategy(strategy_generator.strategy_name)

    strat_result = strategy_generator.strategy_parser(model)

    for (from_player, to_player) in strat_result:
        print(str(from_player.num) + " to " + str(to_player.num))


def find_applicable_strat(world_view) -> StrategyGenerator:
    # Simple passing model is only applicable if 1 player is in possession of the ball
    play_in_poss: int = 0
    for play in world_view.players:
        if play.has_ball:
            play_in_poss += 1

    if play_in_poss == 1:
        return StrategyGenerator("PassingModel", _update_passing_model, extract_passes)

    return None


def _update_passing_model(wv, model: UppaalModel):
    '''
    UPPAAL current setup
    player0 = TeamPlayer(0, 10, 10, true);
    player1 = TeamPlayer(1, 15, 15, false);
    player2 = TeamPlayer(2, 45, 10, false);
    player3 = TeamPlayer(3, 30, 10, false);
    player4 = TeamPlayer(4, 60, 10, false);
    '''
    closest_players: [PlayerViewCoach] = wv.get_closest_team_players_to_ball(5)
    closest_opponents: [PlayerViewCoach] = wv.get_closest_opponents(closest_players, 5)

    for i in range(len(closest_players)):
        model.set_system_decl_arguments(SYSTEM_PLAYER_NAMES[i], [i])

    model.set_global_declaration_value(PLAYER_POS_DECL_NAME, to_2d_array_decl(closest_players))
    model.set_global_declaration_value(OPPONENT_POS_DECL_NAME, to_2d_array_decl(closest_opponents))

    return closest_players


def get_ball_possessor(regressor: Regressor, locations, team_members):
    for i, player in enumerate(team_members):
        state_name = SYSTEM_PLAYER_NAMES[i] + ".location"
        possession_location_id = locations[state_name + ".InPossesion"]
        if int(regressor.get_value(state_name)) == int(possession_location_id):
            return player
    return -1


def get_pass_target(r, index_to_transition_dict, team_members):
    action = index_to_transition_dict[str(r.get_highest_val_trans()[0])]
    target = int(re.search("pass_target := ([0-4])", action).group(1))
    return team_members[target]


def extract_passes(strategy: UppaalStrategy, team_members):
    passes = []

    for r in strategy.regressors:
        from_player = get_ball_possessor(r, strategy.location_to_id, team_members)
        to_player = get_pass_target(r, strategy.index_to_transition, team_members)
        passes.append((from_player, to_player))

    return passes


def to_2d_array_decl(players : [PlayerViewCoach]):
    string = "{"
    separator = ""
    for player in players:
        string += separator + "{" + str(player.coord.pos_x) + ", " + str(player.coord.pos_y) + "}"
        separator = ","  # Only comma separate after first coordinate
    return string + "}"


"""
wv = WorldViewCoach(0, "Team1")
wv.ball = BallOnlineCoach(Coordinate(0, 0), 0, 0)
wv.players.append(PlayerViewCoach("Team1", "0", False, Coordinate(6, 10), 0, 0, 0, 0, True))
wv.players.append(PlayerViewCoach("Team1", "1", False, Coordinate(10, 22), 0, 0, 0, 0, False))
wv.players.append(PlayerViewCoach("Team1", "2", False, Coordinate(26, 18), 0, 0, 0, 0, False))
wv.players.append(PlayerViewCoach("Team1", "3", False, Coordinate(32, 18), 0, 0, 0, 0, False))
wv.players.append(PlayerViewCoach("Team1", "4", False, Coordinate(26, 12), 0, 0, 0, 0, False))
wv.players.append(PlayerViewCoach("Team2", "0", False, Coordinate(16, 20), 0, 0, 0, 0, False))
wv.players.append(PlayerViewCoach("Team2", "1", False, Coordinate(28, 18), 0, 0, 0, 0, False))
wv.players.append(PlayerViewCoach("Team2", "2", False, Coordinate(14, 12), 0, 0, 0, 0, False))
wv.players.append(PlayerViewCoach("Team2", "3", False, Coordinate(28, 18), 0, 0, 0, 0, False))
wv.players.append(PlayerViewCoach("Team2", "4", False, Coordinate(14, 22), 0, 0, 0, 0, False))
generate_strategy(wv)"""
'''
EMPTY_SPACE = " *\n *"
'"locationnames":{(("[^"]*":{[^}]*})*,?)*}'
'''