import math
import re

from coaches.world_objects_coach import WorldViewCoach, PlayerViewCoach
from constants import SECONDS_BETWEEN_STAMINA_STRAT, USING_STAMINA_MODEL
from uppaal.uppaal_model import UppaalModel, UppaalStrategy, execute_verifyta, Regressor
from player.player import WorldView, PlayerState

SYSTEM_PLAYER_NAMES = ["player0", "player1", "player2", "player3", "player4"]
PLAYER_POS_DECL_NAME = "player_pos[team_members][2]"
OPPONENT_POS_DECL_NAME = "opponent_pos[opponents][2]"


def generate_strategy_player(state: PlayerState):
    strategy_generator = _find_applicable_strat_player(state)
    if strategy_generator is None:
        return

    return strategy_generator.generate_strategy(state)


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
        # wv is a player_state for player strats!
        model_data = self._model_modifier(wv, model)

        execute_verifyta(model)

        # Extract strategy
        uppaal_strategy = UppaalStrategy(self.strategy_name)

        # Interpret strategy and produce coach /say output
        return self._strategy_parser(uppaal_strategy, model_data)

def has_applicable_strat(wv: WorldViewCoach) -> bool:
    if _find_applicable_strat(wv) is not None:
        return True
    return False

def has_applicable_strat_player(state: PlayerState):
    if _find_applicable_strat_player(state) is not None:
        return True
    return False


def _find_applicable_strat_player(state: PlayerState) -> _StrategyGenerator:
    if USING_STAMINA_MODEL and state.now() % (SECONDS_BETWEEN_STAMINA_STRAT * 10) == 2 + int(state.num) * 5:
        return _StrategyGenerator("/staminamodel/staminamodel{0}{1}".format(state.world_view.side, state.num),
                                  _update_stamina_model_simple, _extract_stamina_solution_simple)
    return None


def _find_applicable_strat(world_view) -> _StrategyGenerator:
    # Simple passing model is only applicable if 1 player is in possession of the ball
    play_in_poss: int = 0
    for play in world_view.players:
        if play.has_ball and play.team == world_view.team:
            play_in_poss += 1

    if play_in_poss == 1:
        return _StrategyGenerator("PassingModel", _update_passing_model, _extract_actions)

    return None

def _update_stamina_model_simple(state: PlayerState, model: UppaalModel):
    dashes_since_last_strat = state.body_state.dash_count - state.action_history.dashes_last_stamina_strat
    state.action_history.dashes_last_stamina_strat = state.body_state.dash_count

    model.set_global_declaration_value("recovery_rate_per_sec", 300)
    model.set_global_declaration_value("dashes_last_strategy", dashes_since_last_strat)
    model.set_global_declaration_value("seconds_per_strategy", SECONDS_BETWEEN_STAMINA_STRAT)

    return state.body_state.stamina

def _extract_stamina_solution_simple(strategy: UppaalStrategy, current_stamina: int):
    current_stamina_interval: int = math.floor(current_stamina / 1000)

    for r in strategy.regressors:
        if int(r.get_value("stamina_interval")) == current_stamina_interval:
            highest_dash: str = str(r.get_highest_val_trans())
            print("Result dash power: ", highest_dash)
            return "(dash_power {0})".format(highest_dash[highest_dash.find("(") + 1:highest_dash.find(",")])


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


def _extract_actions(strategy: UppaalStrategy, team_members):
    actions = []

    for r in strategy.regressors:
        if "Passing" in str(strategy.index_to_transition[r.get_highest_val_trans()[0]]):
            from_player = _get_ball_possessor(r, strategy.location_to_id, team_members)
            to_player = _get_pass_target(r, strategy.index_to_transition, team_members)
            actions.append("(" + str(from_player.num) + " pass " + str(to_player.num) + ")")
        else:
            from_player = _get_ball_possessor(r, strategy.location_to_id, team_members)
            actions.append("(" + str(from_player.num) + " dribble" + ")")

    return actions


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