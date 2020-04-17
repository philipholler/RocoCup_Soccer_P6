import subprocess
import time
import re
import codecs
from os import fdopen, remove

from shutil import copymode, move
from tempfile import mkstemp

from coach.world_objects_coach import WorldViewCoach, PlayerViewCoach, BallOnlineCoach
from player.playerstrategy import PlayerStrategy
from uppaal.regressor import Regressor
from uppaal.uppaal_model import UppaalModel, UppaalStrategy
from uppaal import VERIFYTA_MODELS_PATH, VERIFYTA_OUTPUT_DIR_PATH, VERIFYTA_QUERIES_PATH, VERIFYTA_PATH
from player.world_objects import Coordinate

SYSTEM_PLAYER_NAMES = ["player0", "player1", "player2", "player3", "player4"]
PLAYER_POS_DECL_NAME = "player_pos[team_members][2]"
OPPONENT_POS_DECL_NAME = "opponent_pos[opponents][2]"


def generate_strategy(wv: WorldViewCoach):
    applicable_strat = find_applicable_strat(wv)
    if applicable_strat is None:
        return
    xml_file_name = applicable_strat + ".xml"
    queries_file_name = applicable_strat + ".q"

    # Create model
    model = UppaalModel(xml_file_name)
    # Update model according to world view. Only works for SimplePassingModel currently.
    model_team_members = _update_passing_model(wv, model, xml_file_name)

    # Update queries files with the right path
    path_to_strat_file = _update_queries_write_path(str(VERIFYTA_QUERIES_PATH / queries_file_name))

    # Generate command to generate strategy
    # verifyta_path --print-strategies outputdir xml_path queries_dir learning-method?
    command = "{0} {1} {2}".format(VERIFYTA_PATH, VERIFYTA_MODELS_PATH / xml_file_name
                                   , VERIFYTA_QUERIES_PATH / queries_file_name)

    # Run uppaal verifyta command line tool
    verifyta = subprocess.Popen(command, shell=True)

    # Wait for uppaal to finish generating and printing strategy
    while verifyta.poll() is None:
        time.sleep(0.001)

    # Create strategy representation
    strategy = parse_strategy(VERIFYTA_OUTPUT_DIR_PATH / path_to_strat_file)


    pass_list = extract_passes(strategy, model_team_members)

    for (from_player, to_player) in pass_list:
        print(str(from_player.num) + " to " + str(to_player.num))


def find_applicable_strat(wv):
    # Simple passing model is only applicable if 1 player is in possession of the ball
    play_in_poss: int = 0
    for play in wv.players:
        if play.has_ball:
            play_in_poss += 1

    if play_in_poss == 1:
        return "PassingModel"

    return None


def get_ball_possessor(regressor: Regressor, locations, team_members):
    for i in range(0, len(team_members)):
        state_name = SYSTEM_PLAYER_NAMES[i] + ".location"
        possesion_location_id = locations[state_name + ".InPossesion"]
        if int(regressor.get_value(state_name)) == int(possesion_location_id):
            return team_members[i]
    return -1


def add_location_mappings(location_to_index, template_name, mappings):
    index_location_pattern = r'"([0-9]*)":"([^"]*)"'
    indices_and_locations = re.findall(index_location_pattern, mappings)

    for (index, location) in indices_and_locations:
        location_to_index[template_name + "." + location] = index


def _extract_location_ids(strategy: str):
    location_name_to_id = {}
    all_template_pattern = r'"locationnames":\{(.*)\},"r'
    all_templates = re.search(all_template_pattern, strategy, re.DOTALL).group(1)

    individual_template_pattern = r'"([^"]*)":\{([^\}]*)\}'
    template_and_mappings = re.findall(individual_template_pattern, all_templates)

    for (template_name, mappings) in template_and_mappings:
        add_location_mappings(location_name_to_id, template_name, mappings)

    return location_name_to_id


def get_pass_target(r, index_to_transition_dict, team_members):
    action = index_to_transition_dict[str(r.get_highest_val_trans()[0])]
    target = int(re.search("pass_target := ([0-4])", action).group(1))
    return team_members[target]


def parse_strategy(path_to_strategy_file):
    strategy_text = ""
    with open(path_to_strategy_file, 'r') as f:
        for line in f:
            strategy_text += line

    index_to_transition: {} = _extract_transition_dict(strategy_text)
    statevar_to_index: {} = _extract_statevars_to_index_dict(strategy_text)
    location_to_id: {} = _extract_location_ids(strategy_text)
    regressors: [] = _extract_regressors(strategy_text, statevar_to_index)

    return UppaalStrategy(location_to_id, index_to_transition, statevar_to_index, regressors)


def extract_passes(strategy: UppaalStrategy, team_members):
    passes = []

    for r in strategy.regressors:
        from_player = get_ball_possessor(r, strategy.location_to_id, team_members)
        to_player = get_pass_target(r, strategy.index_to_action, team_members)
        passes.append((from_player, to_player))

    return passes


def _update_queries_write_path(query_path):
    with open(query_path, 'r', encoding='utf8') as f:
        for l in f:
            stripped_line = l.strip()
            if stripped_line.startswith("saveStrategy"):
                strat = re.search(',.*\)', stripped_line)
                strat_name = strat.group(0)[1:-1]
                new_strat_file_name = re.search('/[^/]*"', stripped_line)
                strat_file_name = new_strat_file_name.group(0)[1:-1]
                newline = 'saveStrategy("' + str(
                    VERIFYTA_OUTPUT_DIR_PATH / strat_file_name) + '",' + strat_name + ')' + '\n'
                _replace_in_file(query_path, l, newline)
                # This does not work for more than one saveStrategy call
                break

    return str(VERIFYTA_OUTPUT_DIR_PATH / strat_file_name)


def _replace_in_file(file_path, pattern, subst):
    # Create temp file
    fh, abs_path = mkstemp()
    with fdopen(fh, 'w', encoding='utf8') as new_file:
        with open(file_path, encoding='utf8') as old_file:
            for line in old_file:
                new_file.write(line.replace(pattern, subst))
    # Copy the file permissions from the old file to the new file
    copymode(file_path, abs_path)
    # Remove original file
    remove(file_path)
    # Move new file
    move(abs_path, file_path)


def to_2d_array_decl(players : [PlayerViewCoach]):
    string = "{"
    separator = ""
    for player in players:
        string += separator + "{" + str(player.coord.pos_x) + ", " + str(player.coord.pos_y) + "}"
        separator = ","  # Only comma separate after first coordinate
    return string + "}"


def _update_passing_model(wv, model: UppaalModel, xml_file_name):
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

    for i in range(0, len(closest_players)):
        model.set_system_decl_arguments(SYSTEM_PLAYER_NAMES[i], [i])

    model.set_global_declaration_value(PLAYER_POS_DECL_NAME, to_2d_array_decl(closest_players))
    model.set_global_declaration_value(OPPONENT_POS_DECL_NAME, to_2d_array_decl(closest_opponents))
    model.save_xml_file(xml_file_name)

    return closest_players


def _extract_regressors(strat_string, state_vars_to_index_dict: {}):
    final_regressors = []
    # Get regressors part of strategy
    regre_text = re.search(r'"regressors":\{.*\}', strat_string, re.DOTALL)
    # Remove "regressors":{ and }
    regre_text = regre_text.group(0)[14:-1].strip()
    # Find each regressor
    regressors = regre_text.split('},')
    # Strip all elements from empty spaces
    regressors = [w.strip() for w in regressors]

    for reg in regressors:
        # Get statevars value like: "(2,0,1,0,1,0,-1,1,1,0,0,0,0,0)"
        statevars_vals = re.search(r'"\([-0-9,]*\)"', reg, re.DOTALL).group(0)
        statevars_vals = statevars_vals.replace("(", "").replace('"', "").replace(")", "")
        statevars_vals = statevars_vals.split(",")
        # Get pairs of transitions and values like ['2:89.09999999999999', '0:0']
        trans_val_text = re.search(r'"regressor":[\t\n]*\{[^}]*\}', reg, re.DOTALL)
        trans_val_text = trans_val_text.group(0)[13:-1].strip()
        trans_val_pairs = [w.strip().replace("\n", "").replace("\t", "").replace('"', '').replace('{', "") for w in
                           trans_val_text.split(',')]
        # The final list of pairs
        format_trans_val_pairs = []
        for pair in trans_val_pairs:
            cur_pair = pair.split(":")
            format_trans_val_pairs.append((int(cur_pair[0]), float(cur_pair[1])))

        new_regressor = Regressor(statevars_vals, format_trans_val_pairs, state_vars_to_index_dict)
        final_regressors.append(new_regressor)

    return final_regressors


def _extract_transition_dict(strat_string):
    trans_dict = {}
    # Get actions part of strategy
    act_text = re.search(r'"actions":\{.*\},"s', strat_string, re.DOTALL)
    # Remove "actions":{ and },"s
    act_text = act_text.group(0)[11:-4].strip()
    # Create list by separating at commas
    act_lines = act_text.split('\n')
    # Strip all elements from empty spaces
    act_lines = [w.strip() for w in act_lines]

    for l in act_lines:
        matches = re.findall(r'"[^\"]*"', l, re.DOTALL)
        index = str(matches[0]).replace('"', "")
        value = str(matches[1]).replace('"', "")
        trans_dict[index] = value

    return trans_dict


def _extract_statevars_to_index_dict(strat_string) -> {}:
    # Get statevars part of strategy
    statevars = re.search(r'"statevars":\[[^\]]*\]', strat_string, re.DOTALL)
    # Remove "statevars":[ and ]
    statevars = statevars.group(0).split('[')[1].split(']')[0]
    # Create list by separating at commas
    statevars = statevars.split(',')
    # Strip all elements from empty spaces and quotes
    statevars = [w.strip()[1:-1] for w in statevars]

    statevar_name_to_index_dict = {}
    i = 0
    for statevar in statevars:
        statevar_name_to_index_dict[statevar] = i
        i += 1

    return statevar_name_to_index_dict

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
generate_strategy(wv)
'''
EMPTY_SPACE = " *\n *"
'"locationnames":{(("[^"]*":{[^}]*})*,?)*}'
'''