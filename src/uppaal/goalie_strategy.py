import time
from math import floor
import json

from geometry import Coordinate
from uppaal import STATIC_MODEL_RESULTS
from uppaal.uppaal_model import UppaalModel, execute_verifyta_and_poll, UppaalStrategy, Regressor

GOALIE_STRAT_NAME = "GoaliePositioning"

GOALIE_AREA = (Coordinate(47, -9), Coordinate(52.5, 9))
STRIKER_AREA = (Coordinate(36, -20), Coordinate(50.0, 20))

STEPS_PER_METER = 1


def _synthesise_move_direction(goalie_position, striker_position):
    # Update xml file with player positions
    model = UppaalModel("/" + GOALIE_STRAT_NAME)
    model.set_global_declaration_value("play_pos_x", goalie_position[0])
    model.set_global_declaration_value("play_pos_y", goalie_position[1])
    model.set_global_declaration_value("op_pos_x", striker_position[0])
    model.set_global_declaration_value("op_pos_y", striker_position[1])

    # Synthesize strategy using uppaal
    execute_verifyta_and_poll(model)

    # Extract synthesized strategy
    strategy = UppaalStrategy("/" + GOALIE_STRAT_NAME)

    state_var_names: [str] = []
    for name in state_var_names:
        state_var_names.append(name)

    # Get (0,0,0,0,0,0) regressors
    zero_reg: Regressor = None
    for r in strategy.regressors:
        if all(int(i) == 0 for i in r.state_var_values):
            if zero_reg == None:
                zero_reg = r
            else:
                raise Exception("(0,0,0,0,0,0) regressor is being overwritten. Must have been present twice!")

    # Get min regressor
    min_reg = zero_reg.get_lowest_val_trans()

    # Get minimum value regressor transition
    min_reg_trans: str = strategy.index_to_transition.get(min_reg[0])

    """
    Possibilities:
    "0":"player.choose_y->player._id1 { speed_y == 0, tau, speed_y := speed_y + MOVE_SPEED }",
    "1":"player.choose_y->player._id1 { speed_y == 0, tau, speed_y := speed_y - MOVE_SPEED }",
    "2":"player.choose_x->player.choose_y { 1, tau, 1 }",
    "3":"player.choose_y->player._id1 { 1, tau, 1 }",
    "4":"player.choose_x->player.choose_y { speed_x == 0, tau, speed_x := speed_x - MOVE_SPEED }",
    "5":"player.choose_x->player.choose_y { speed_x == 0, tau, speed_x := speed_x + MOVE_SPEED }",
    "6":"WAIT"
    """
    # Extract data from transition
    # If moving up
    if "speed_y +" in min_reg_trans:
        return 270
    # Moving down
    elif "speed_y -" in min_reg_trans:
        return 90
    # Moving toward the right (inside goal)
    elif "speed_x +" in min_reg_trans:
        return 0
    # Moving to the left (out from the goal)
    elif "speed_x -" in min_reg_trans:
        return 180
    # If should wait
    elif "WAIT" not in min_reg_trans:
        return None
    else:
        raise Exception("Could not find movement direction from regressors: " + strategy.regressors)


def _generate_positions(bound: (Coordinate, Coordinate), steps_per_meter):
    width = bound[1].pos_x - bound[0].pos_x
    height = bound[1].pos_y - bound[0].pos_y
    positions = []

    for x in range(round(width * steps_per_meter)):
        for y in range(round(height * steps_per_meter)):
            positions.append((bound[0].pos_x + x * 1 / steps_per_meter, bound[0].pos_y + y * 1 / steps_per_meter))

    return positions


def _convert_coordinate(coord: Coordinate, steps_per_meter):
    new_x = floor(coord.pos_x / steps_per_meter) * steps_per_meter
    new_y = floor(coord.pos_y / steps_per_meter) * steps_per_meter
    return Coordinate(new_x, new_y)


def get_result_dict() -> {}:
    with open(str(STATIC_MODEL_RESULTS) + '/GoaliePositioning.json') as fp:
        new_dict = json.load(fp)
    return new_dict


if __name__ == "__main__":
    player_coord_keys = _generate_positions(STRIKER_AREA, STEPS_PER_METER)
    goalie_coord_keys = _generate_positions(GOALIE_AREA, STEPS_PER_METER)

    # Adjust uppaal model positions to be at the center of the square
    player_positions = list(
        map(lambda key: (key[0] + STEPS_PER_METER / 2, key[1] + STEPS_PER_METER / 2), player_coord_keys))
    goalie_positions = list(
        map(lambda key: (key[0] + STEPS_PER_METER / 2, key[1] + STEPS_PER_METER / 2), goalie_coord_keys))

    pos_to_act_dict = {}
    before = int(time.time())
    i = 0
    combinations = len(player_positions) * len(goalie_positions)
    for player_position in player_positions:
        for goalie_position in goalie_positions:
            result = _synthesise_move_direction(goalie_position, player_position)
            pos_to_act_dict[str(str(player_position) + "," + str(goalie_position))] = result
            i += 1
            if i == 10:
                break
            print("Doing {0} of {1}".format(str(i), str(combinations)))
        break
    after = int(time.time())

    print("Time elapsed in seconds: {}".format(str(after - before)))

    with open(str(STATIC_MODEL_RESULTS) + '/GoaliePositioning.json', 'w') as fp:
        json.dump(pos_to_act_dict, fp)
