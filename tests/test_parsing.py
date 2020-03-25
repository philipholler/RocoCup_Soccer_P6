from unittest import TestCase
import parsing
from player.player import PlayerState
from player.world import Coordinate


class Test(TestCase):
    def test_parse_message_update_state(self):
        ps = PlayerState()
        self.skipTest("Not finished")

    # example: (hear 0 referee kick_off_l)
    def test_parse_hear01(self):
        ps = PlayerState()
        parsing._parse_hear("(hear 0 referee kick_off_l)", ps)
        self.assertEqual(ps.game_state, "kick_off_l", "Game state in the player state should update according to msg")
        self.assertEqual(ps.world_view.sim_time, 0, "Sim time in the player state should update according to msg")

    # todo Fix trilateration tests
    def test_trilateration_horizontally_aligned(self):
        expected_position = Coordinate(19.53533, 21.47515)
        flag_one = parsing.Flag("", Coordinate(10, 15), 11.5, 0)
        flag_two = parsing.Flag("", Coordinate(40, 15), 21.5, 0)

        (first_solution, second_solution) = parsing._solve_trilateration(flag_one, flag_two)
        first_solution_correct = is_same_coordinate(first_solution, expected_position)
        second_solution_correct = is_same_coordinate(second_solution, expected_position)

        self.assertTrue(first_solution_correct or second_solution_correct)

    def test_trilateration_horizontally_aligned_both_negative(self):
        expected_position = Coordinate(-20, 10)
        flag_one = parsing.Flag("", Coordinate(-40, 0.0), 22.36, 0)
        flag_two = parsing.Flag("", Coordinate(-10, 0.0), 14.14, 0)

        (first_solution, second_solution) = parsing._solve_trilateration(flag_one, flag_two)
        first_solution_correct = is_same_coordinate(first_solution, expected_position)
        second_solution_correct = is_same_coordinate(second_solution, expected_position)

        self.assertTrue(first_solution_correct or second_solution_correct)

    def test_trilateration_horizontally_misaligned_negative_and_positive(self):
        expected_position = Coordinate(0, -5)
        flag_one = parsing.Flag("", Coordinate(5, 5), 11.1803398875, 0)
        flag_two = parsing.Flag("", Coordinate(-15, -10), 15.8113883008, 0)

        (first_solution, second_solution) = parsing._solve_trilateration(flag_one, flag_two)
        first_solution_correct = is_same_coordinate(first_solution, expected_position)
        second_solution_correct = is_same_coordinate(second_solution, expected_position)

        self.assertTrue(first_solution_correct or second_solution_correct)

    def test_trilateration_order_reversed(self):
        flag_one = parsing.Flag("", Coordinate(0, 0), 11.5, 0)
        flag_two = parsing.Flag("", Coordinate(30, 0), 21.5, 0)

        result_1 = parsing._solve_trilateration(flag_one, flag_two)
        result_2 = parsing._solve_trilateration(flag_two, flag_one)

        self.assertTrue(is_same_coordinate(result_1[0], result_2[0]) or is_same_coordinate(result_1[0], result_2[1]))
        self.assertTrue(is_same_coordinate(result_1[1], result_2[0]) or is_same_coordinate(result_1[1], result_2[1]))


def is_same_coordinate(c1, c2, precision=0.1):
    difference = c1 - c2
    return abs(difference.pos_y) <= precision and abs(difference.pos_x) < precision


