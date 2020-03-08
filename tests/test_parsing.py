from unittest import TestCase
import parsing
import player_state
from world import Coordinate


class Test(TestCase):
    def test_parse_message_update_state(self):
        ps = player_state.PlayerState()
        self.skipTest("Not finished")

    # example: (hear 0 referee kick_off_l)
    def test_parse_hear01(self):
        ps = player_state.PlayerState()
        parsing.parse_hear("(hear 0 referee kick_off_l)", ps)
        self.assertEqual(ps.game_state, "kick_off_l", "Game state in the player state should update according to msg")
        self.assertEqual(ps.sim_time, str(0), "Sim time in the player state should update according to msg")

    def test_trilateration_horizontally_aligned_flags(self):
        expected_position = Coordinate(9.53533, 6.47515)
        flag_one = (Coordinate(0, 0), 11.5)
        flag_two = (Coordinate(30, 0), 21.5)

        parsing.approximate_position([flag_one, flag_two])
        self.skipTest("Not finished")
