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

    # Initial statevar values
    state_var_values: [] = [0, 0, 0, 0, 0, 0]

    # Get value of statevar when both play and opponent are in x
    player_choose_x_state_index = strategy.location_to_id["player.location.choose_x"]
    opponent_choose_x_state_index = strategy.location_to_id["opponent.location.choose_x"]
    state_var_values[strategy.statevar_to_index["player.location"]] = int(player_choose_x_state_index)
    state_var_values[strategy.statevar_to_index["opponent.location"]] = int(opponent_choose_x_state_index)

    init_regressor: Regressor = strategy.get_regressor_with_statevar_values(state_var_values)

    # Get min regressor for to get decision
    min_reg_zero_reg = init_regressor.get_lowest_val_trans()
    # Get minimum value regressor transition
    min_reg_trans_zero_reg: str = strategy.index_to_transition.get(min_reg_zero_reg[0])

    # Moving toward the right (inside goal)
    if "speed_x +" in min_reg_trans_zero_reg:
        x_movement = 1
    # Moving to the left (out from the goal)
    elif "speed_x -" in min_reg_trans_zero_reg:
        x_movement = -1
    else:
        x_movement = 0

    if x_movement == 1:
        state_var_values[strategy.statevar_to_index["player.speed_x"]] = 1
    elif x_movement == -1:
        state_var_values[strategy.statevar_to_index["player.speed_x"]] = -1

    # Change player location state var
    player_choose_y_state_index = strategy.location_to_id["player.location.choose_y"]
    state_var_values[strategy.statevar_to_index["player.location"]] = int(player_choose_y_state_index)

    # Now that the statevars are updated according to the decision made, we can the regressor from the new state
    # Get the new regressor according to the new statevar values
    after_1_decision_reg: Regressor = strategy.get_regressor_with_statevar_values(state_var_values)

    # Get min regressor for to get decision
    min_reg_zero_reg = after_1_decision_reg.get_lowest_val_trans()
    # Get minimum value regressor transition
    min_reg_trans_zero_reg: str = strategy.index_to_transition.get(min_reg_zero_reg[0])

    if "speed_y +" in min_reg_trans_zero_reg:
        y_movement = 1
    # Moving to the left (out from the goal)
    elif "speed_y -" in min_reg_trans_zero_reg:
        y_movement = -1
    else:
        y_movement = 0

    return x_movement, y_movement


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
    for player_pos in range(0, len(player_positions)):
        for goalie_pos in range(0, len(goalie_positions)):
            result = _synthesise_move_direction(goalie_positions[goalie_pos], player_positions[player_pos])
            print("With goalie={0} and player={1}".format(goalie_positions[goalie_pos], player_positions[player_pos]))
            pos_to_act_dict[str(str(goalie_coord_keys[goalie_pos]) + "," + str(player_coord_keys[player_pos]))] = result
            i += 1
            print("Doing {0} of {1}".format(str(i), str(combinations)))
        with open(str(STATIC_MODEL_RESULTS) + '/GoaliePositioning.json', 'w') as fp:
            json.dump(pos_to_act_dict, fp)
    after = int(time.time())
    print("Time elapsed in seconds: {}".format(str(after - before)))


    with open(str(STATIC_MODEL_RESULTS) + '/GoaliePositioning.json', 'w') as fp:
        json.dump(pos_to_act_dict, fp)
