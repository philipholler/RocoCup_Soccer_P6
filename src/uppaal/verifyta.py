import subprocess
import time
import re
import codecs
from os import fdopen, remove

from shutil import copymode, move
from tempfile import mkstemp

from coach.world_objects_coach import WorldViewCoach, PlayerViewCoach, BallOnlineCoach
from uppaal.regressor import Regressor
from uppaal.uppaal_model import UPPAAL_MODEL
from uppaal import VERIFYTA_MODELS_PATH, VERIFYTA_OUTPUT_DIR_PATH, VERIFYTA_QUERIES_PATH, VERIFYTA_PATH
from player.world_objects import Coordinate


def generate_strategy(wv: WorldViewCoach):
    applicable_strat = find_applicable_strat(wv)
    if applicable_strat is None:
        return
    xml_file_name = applicable_strat + ".xml"
    queries_file_name = applicable_strat + ".q"

    # Create model
    model = UPPAAL_MODEL(xml_file_name)
    # Update model according to world view. Only works for SimplePassingModel currently.
    _update_model(wv, model, xml_file_name)

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

    # 3. Input strategy to coach
    passing_list = parse_passing_strat(path_to_strat_file)
    # todo create representation of strategy and input to coach. Maybe return as object? - Philip
    return


def find_applicable_strat(wv):
    # Simple passing model is only applicable if 1 player is in possession of the ball
    play_in_poss: int = 0
    for play in wv.players:
        if play.has_ball:
            play_in_poss += 1

    if play_in_poss == 1:
        return "SimplePassingModel"

    return None


def parse_passing_strat(path_to_strat_file):
    strat_string = ""
    with open(path_to_strat_file, 'r') as f:
        for l in f:
            strat_string = strat_string + l

    index_to_transition_dict: {} = _extract_transition_dict(strat_string)

    statevars: [] = _extract_statevars(strat_string)

    regressors: [] = _extract_regressors(strat_string)
    print(regressors)

    return []


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


def _update_model(wv, model: UPPAAL_MODEL, xml_file_name):
    '''
    UPPAAL current setup
    player0 = TeamPlayer(0, 10, 10, true);
    player1 = TeamPlayer(1, 15, 15, false);
    player2 = TeamPlayer(2, 45, 10, false);
    player3 = TeamPlayer(3, 30, 10, false);
    player4 = TeamPlayer(4, 60, 10, false);
    '''

    five_closest_players: [PlayerViewCoach] = wv.get_closest_team_players_to_ball(5)
    sys_decl_names = ["player0", "player1", "player2", "player3", "player4"]
    # Arguments:
    # const player_id_t id, const int pos_x, const int pos_y, bool has_ball
    for play in five_closest_players:
        if play.has_ball:
            model.set_arguments(sys_decl_names.pop(0), [play.num, play.coord.pos_x, play.coord.pos_y, 'true'])
        else:
            model.set_arguments(sys_decl_names.pop(0), [play.num, play.coord.pos_x, play.coord.pos_y, 'false'])

    model.save_xml_file(xml_file_name)


def _extract_regressors(strat_string):
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
        trans_val_pairs = [w.strip().replace("\n", "").replace("\t", "").replace('"', '').replace('{', "") for w in trans_val_text.split(',')]
        # The final list of pairs
        format_trans_val_pairs = []
        for pair in trans_val_pairs:
            cur_pair = pair.split(":")
            format_trans_val_pairs.append((int(cur_pair[0]), float(cur_pair[1])))

        new_regressor = Regressor(statevars_vals, format_trans_val_pairs)
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


def _extract_statevars(strat_string):
    # Get statevars part of strategy
    statevars = re.search(r'"statevars":\[[^\]]*\]', strat_string, re.DOTALL)
    # Remove "statevars":[ and ]
    statevars = statevars.group(0).split('[')[1].split(']')[0]
    # Create list by separating at commas
    statevars = statevars.split(',')
    # Strip all elements from empty spaces and quotes
    statevars = [w.strip()[1:-1] for w in statevars]

    return statevars


wv = WorldViewCoach(0, "Team1")
wv.ball = BallOnlineCoach(Coordinate(0, 0), 0, 0)
p = PlayerViewCoach("Team1", "1", False, Coordinate(0, 0), 0, 0, 0, 0, True)
wv.players.append(p)
generate_strategy(wv)



