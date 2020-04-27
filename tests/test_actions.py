from unittest import TestCase

from player.actions import calculate_kick_power
from player.player import PlayerState
from player.world_objects import Ball, PrecariousData, Coordinate


class Test(TestCase):
    def test_calculate_kick_power_01(self):
        ball = Ball(0.7, 180, 0, 0, Coordinate(0, 0), PrecariousData.unknown(), PrecariousData.unknown())
        ps = PlayerState()
        ps.world_view.ball.set_value(ball, 0)
        distance = 17
        self.assertTrue(calculate_kick_power(ps, distance) > 100, "Should not be able to kick 17 meters with worst "
                                                                  "case ball position")

    def test_calculate_kick_power_02(self):
        ball = Ball(0, 0, 0, 0, Coordinate(0, 0), PrecariousData.unknown(), PrecariousData.unknown())
        ps = PlayerState()
        ps.world_view.ball.set_value(ball, 0)
        distance = 43
        self.assertTrue(calculate_kick_power(ps, distance) < 100, "Should be able to kick 43 meters with optimal ball "
                                                                  "position")

    def test_calculate_kick_power_03(self):
        ball = Ball(0.4, 90, 0, 0, Coordinate(0, 0), PrecariousData.unknown(), PrecariousData.unknown())
        ps = PlayerState()
        ps.world_view.ball.set_value(ball, 0)
        distance = 30
        self.assertTrue(calculate_kick_power(ps, distance) < 100, "Should be able to kick 30 meters with"
                                                                  " decent ball position")
