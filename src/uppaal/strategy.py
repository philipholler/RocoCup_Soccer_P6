import re

from coaches.world_objects_coach import WorldViewCoach, PlayerViewCoach
from uppaal.uppaal_model import UppaalModel, UppaalStrategy, execute_verifyta, Regressor
from player.player import WorldView


SYSTEM_PLAYER_NAMES = ["player0", "player1", "player2", "player3", "player4"]
PLAYER_POS_DECL_NAME = "player_pos[team_members][2]"
OPPONENT_POS_DECL_NAME = "opponent_pos[opponents][2]"


def generate_strategy_player(wv: WorldView):
    strategy_generator = _find_applicable_strat_player(wv)
    if strategy_generator is None:
        return

    return strategy_generator.generate_strategy(wv)


def generate_strategy(wv: WorldViewCoach):
    strategy_generator = _find_applicable_strat(wv)
    if strategy_generator is None:
        return

    return strategy_generator.generate_strategy(wv)


class _StrategyGenerator:

    def __init__(self, strategy_name, model_modifier, strategy_parser) -> None:
        super().__init__()
        self.strategy_name = strategy_name
        self.strategy_name = strategy_name
        self._strategy_parser = strategy_parser
        self._model_modifier = model_modifier

    def generate_strategy(self, wv):
        # Create model
        model = UppaalModel(self.strategy_name)

        # Update model data in accordance with chosen strategy and execute verifyta
        model_data = self._model_modifier(wv, model)

        execute_verifyta(model)

        # Extract strategy
        uppaal_strategy = UppaalStrategy(self.strategy_name)

        # Interpret strategy and produce coach /say output
        return self._strategy_parser(uppaal_strategy, model_data)


def _find_applicable_strat_player(wv) -> _StrategyGenerator:
    # todo use player specific strategies once made available - Philip
    pass


def _find_applicable_strat(world_view) -> _StrategyGenerator:
    # Simple passing model is only applicable if 1 player is in possession of the ball
    play_in_poss: int = 0
    for play in world_view.players:
        if play.has_ball and play.team == world_view.team:
            play_in_poss += 1

    if play_in_poss == 1:
        return _StrategyGenerator("PassingModel", _update_passing_model, _extract_passes)

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

    model.set_global_declaration_value(PLAYER_POS_DECL_NAME, _to_2d_int_array_decl(closest_players))
    model.set_global_declaration_value(OPPONENT_POS_DECL_NAME, _to_2d_int_array_decl(closest_opponents))

    return closest_players


def _extract_passes(strategy: UppaalStrategy, team_members):
    passes = []

    for r in strategy.regressors:
        from_player = _get_ball_possessor(r, strategy.location_to_id, team_members)
        to_player = _get_pass_target(r, strategy.index_to_transition, team_members)
        passes.append("(" + str(from_player.num) + " pass " + str(to_player.num) + ")")

    return passes


def _get_ball_possessor(regressor: Regressor, locations, team_members):
    for i, player in enumerate(team_members):
        state_name = SYSTEM_PLAYER_NAMES[i] + ".location"
        possession_location_id = locations[state_name + ".InPossesion"]
        if int(regressor.get_value(state_name)) == int(possession_location_id):
            return player
    return -1


def _get_pass_target(r, index_to_transition_dict, team_members):
    action = index_to_transition_dict[str(r.get_highest_val_trans()[0])]
    target = int(re.search("pass_target := ([0-9]*)", action).group(1))
    return team_members[target]


def _to_2d_int_array_decl(players: [PlayerViewCoach]):
    string = "{"
    separator = ""
    for player in players:
        string += separator + "{" + str(round(player.coord.pos_x)) + ", " + str(round(player.coord.pos_y)) + "}"
        separator = ","  # Only comma separate after first coordinate
    return string + "}"
