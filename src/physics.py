from sympy.solvers import solve
from sympy import Symbol, Eq, symbols
from player.player import PlayerState
from player.world_objects import Ball, Coordinate, PrecariousData

BALL_DECAY = 0.94  # per tick
BALL_MAX_SPEED = 3
KICKABLE_MARGIN = 0.7
KICK_POWER_RATE = 0.027


def project_ball_position(state: PlayerState, ball: Ball, ticks: int):
    positions: [Coordinate] = []

    def advance(previous_location: Coordinate, vx, vy):
        return Coordinate(previous_location.pos_x + vx, previous_location.pos_y + vy)

    if ball.last_position.is_value_known(state.now() - 5):
        last_position = ball.last_position.get_value()
        delta_time = state.world_view.ball.last_updated_time - ball.last_position.last_updated_time
        velocity_x = ((ball.coord.pos_x - last_position.pos_x) / delta_time) * BALL_DECAY
        velocity_y = ((ball.coord.pos_y - last_position.pos_y) / delta_time) * BALL_DECAY
        positions[0] = advance(ball.coord, velocity_x, velocity_y)
        offset = state.now() - state.world_view.ball.last_updated_time

        for i in range(1, ticks + offset):
            velocity_x *= BALL_DECAY
            velocity_y *= BALL_DECAY
            positions[i] = advance(velocity_x, velocity_y, positions[i - 1])

        return positions[offset:]
    else:
        return []


def calculate_kick_power(state: PlayerState, distance: float) -> int:
    ball: Ball = state.world_view.ball.get_value()
    dir_diff = abs(ball.direction)
    dist_ball = ball.distance
    time_to_target = int(distance * 1.35)

    # Solve for the initial kick power needed to get to the distance after time_to_target ticks
    # x = kickpower (0-100)
    x = Symbol('x', real=True)
    eqn = Eq(sum([(((x * KICK_POWER_RATE) * (1 - 0.25 * (dir_diff / 180) - 0.25 * (dist_ball / KICKABLE_MARGIN)))
                   * BALL_DECAY ** i) for i in range(0, time_to_target)]), distance)
    needed_kick_power = solve(eqn)[0]

    if needed_kick_power < 0:
        raise Exception("Should not be able to be negative. What the hell - Philip")

    return needed_kick_power


ball = Ball(0.7, 180, 0, 0, Coordinate(0, 0), PrecariousData.unknown(), PrecariousData.unknown())
ps = PlayerState()
ps.world_view.ball.set_value(ball, 0)
calculate_kick_power(ps, 17)
