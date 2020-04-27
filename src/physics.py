from player.player import PlayerState
from player.world_objects import Ball, Coordinate

BALL_DECAY = 0.94  # per tick


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
            positions[i] = advance(velocity_x, velocity_y, positions[i-1])

        return positions[offset:]
    else:
        return []
