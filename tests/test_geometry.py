import unittest
from unittest import TestCase
import geometry
from player.world_objects import Coordinate


class Test(TestCase):
    def test_get_object_position01(self):
        # Observer at oregon and ball at 5,5.
        coord: Coordinate = geometry.get_object_position(-45, 7.07, 0, 0, 0)
        delta = 0.1
        self.assertTrue(5 - delta < coord.pos_x < 5 + delta, "Should report the correct position (5,5)")
        self.assertTrue(5 - delta < coord.pos_y < 5 + delta, "Should report the correct position (5,5)")

    def test_get_object_position02(self):
        # Observer at oregon and ball at 5,2.
        coord: Coordinate = geometry.get_object_position(-21.8, 5.39, 0, 0, 0)
        delta = 0.1
        self.assertTrue(5 - delta < coord.pos_x < 5 + delta, "Should report the correct position (5,2)")
        self.assertTrue(2 - delta < coord.pos_y < 2 + delta, "Should report the correct position (5,2)")

    def test_get_object_position03(self):
        # Observer at 1,1 and ball at -2,0.
        coord: Coordinate = geometry.get_object_position(-18.43, 3.16, 1, 1, 180)
        delta = 0.1
        self.assertTrue(-2 - delta < coord.pos_x < -2 + delta, "Should report the correct position (-2,0)")
        self.assertTrue(0 - delta < coord.pos_y < 0 + delta, "Should report the correct position (-2,0)")

    def test_get_object_position04(self):
        # Observer at -2,-3 and ball at -4,1.
        coord: Coordinate = geometry.get_object_position(64.43, 4.47, -2, -3, 180)
        delta = 0.1
        self.assertTrue(-4 - delta < coord.pos_x < -4 + delta, "Should report the correct position (-4,1)")
        self.assertTrue(1 - delta < coord.pos_y < 1 + delta, "Should report the correct position (-4,1)")

    def test_get_object_position05(self):
        # Observer at -2,-3 and ball at 1,1.
        coord: Coordinate = geometry.get_object_position(-53.13, 5, -2, -3, 0)
        delta = 0.1
        self.assertTrue(1 - delta < coord.pos_x < 1 + delta, "Should report the correct position (1,1)")
        self.assertTrue(1 - delta < coord.pos_y < 1 + delta, "Should report the correct position (1,1)")

    # From real example
    # My angle:  249.380770918425 My coord:  (-6.57713520869533, -33.735067104660125) Ball coord:  (-34.21671306111496, -51.94670448684063) Distance:  33.1 , direction:  36
    # In real example, i get (-34.22, -51.95) for some reason???
    def test_get_object_position06(self):
        # Observer at -6.58, -33.74 and ball at 0,0.
        # object_rel_angle: float, dist_to_obj: float, my_x: float, my_y: float, my_global_angle: float
        coord: Coordinate = geometry.get_object_position(36, 34.38, -6.58, -33.74, 245.05)
        delta = 0.1
        self.assertTrue(0 - delta < coord.pos_x < 0 + delta, "Should report the correct position (0,0)")
        self.assertTrue(0 - delta < coord.pos_y < 0 + delta, "Should report the correct position (0,0)")

    def test_smallest_angle_difference(self):
        self.assertEqual(-7, geometry.smallest_angle_difference(354, 1))

    def test_smallest_angle_difference_reverse(self):
        self.assertEqual(7, geometry.smallest_angle_difference(1, 354))

    def test_is_angle_in_range(self):
        self.assertTrue(geometry.is_angle_in_range(15, 0, 359))
        self.assertTrue(geometry.is_angle_in_range(15, 350, 20))
        self.assertTrue(geometry.is_angle_in_range(270, 240, 280))

        self.assertFalse(geometry.is_angle_in_range(240, 260, 280))
        self.assertFalse(geometry.is_angle_in_range(240, 260, 230))

        self.assertFalse(geometry.is_angle_in_range(5, 10, 4))
        self.assertTrue(geometry.is_angle_in_range(3, 10, 4))

