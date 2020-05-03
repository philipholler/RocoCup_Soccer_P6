from unittest import TestCase

from player.actions import calculate_kick_power, stop_ball
from player.player import PlayerState
from player.world_objects import Ball, PrecariousData, Coordinate


class Test(TestCase):
    def test_calculate_kick_power_01(self):
        ball = Ball(0.7, 180, Coordinate(0, 0), 0)
        ps = PlayerState()
        ps.world_view.ball.set_value(ball, 0)
        distance = 17
        self.assertTrue(calculate_kick_power(ps, distance) > 100, "Should not be able to kick 17 meters with worst "
                                                                  "case ball position")

    def test_calculate_kick_power_02(self):
        ball = Ball(0, 0, Coordinate(0, 0), 0)
        ps = PlayerState()
        ps.world_view.ball.set_value(ball, 0)
        distance = 43
        self.assertTrue(calculate_kick_power(ps, distance) < 100, "Should be able to kick 43 meters with optimal ball "
                                                                  "position")

    def test_calculate_kick_power_03(self):
        ball = Ball(0.4, 90, Coordinate(0, 0), 0)
        ps = PlayerState()
        ps.world_view.ball.set_value(ball, 0)
        distance = 30
        self.assertTrue(calculate_kick_power(ps, distance) < 100, "Should be able to kick 30 meters with"
                                                                  " decent ball position")

    def test__calculate_ball_global_dir(self):
        self.skipTest("Ball no longer has 'last_position' attribute")
        state: PlayerState = PlayerState()
        state.body_angle.set_value(90, 1)
        ball: Ball = Ball(0, 0, Coordinate(-1.5, 1.5), 0)
        ball.last_position.set_value(Coordinate(0, 0), 0)
        state.world_view.ball.set_value(ball, 1)
        stop_ball(state)

