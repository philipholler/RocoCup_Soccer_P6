from math import floor

from geometry import Coordinate
from uppaal.uppaal_model import UppaalModel, execute_verifyta_and_poll, UppaalStrategy

KEEPER_STRAT_NAME = "KeeperPositioning"

GOALIE_AREA = (Coordinate(47, -9), Coordinate(52.5, 9))
STRIKER_AREA = (Coordinate(36, -20), Coordinate(50.0, 20))

STEPS_PER_METER = 1


def _synthesise_move_direction(goalie_position, striker_position):
    # Update xml file with player positions
    model = UppaalModel(KEEPER_STRAT_NAME)
    model.set_global_declaration_value("play_pos_x", goalie_position[0])
    model.set_global_declaration_value("play_pos_y", goalie_position[1])
    model.set_global_declaration_value("op_pos_x", striker_position[0])
    model.set_global_declaration_value("op_pos_y", striker_position[1])

    # Synthesize strategy using uppaal
    execute_verifyta_and_poll(model)

    # Extract synthesized strategy
    strategy = UppaalStrategy(KEEPER_STRAT_NAME)
    # TODO : Find correct regressor and extract direction. (Maybe multiple directions based on current speed of opponent?)


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


if __name__ == "__main__":
    player_coord_keys = _generate_positions(GOALIE_AREA, STEPS_PER_METER)
    goalie_coord_keys = _generate_positions(STRIKER_AREA, STEPS_PER_METER)

    # Adjust uppaal model positions to be at the center of the square
    player_positions = map(lambda key: (key[0] + STEPS_PER_METER / 2, key[0] + STEPS_PER_METER / 2), player_coord_keys)
    goalie_positions = map(lambda key: (key[0] + STEPS_PER_METER / 2, key[0] + STEPS_PER_METER / 2), goalie_coord_keys)


    pass
