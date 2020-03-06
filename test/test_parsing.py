from unittest import TestCase
import parsing
import player_state


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