from unittest import TestCase

from geometry import Coordinate
from player.player import ViewFrequency, PlayerState
from player.world_objects import ObservedPlayer, PrecariousData


class TestViewFrequency(TestCase):
    pass


class TestWorldView(TestCase):
    # LEFT SIDE
    def test_get_non_offside_forward_team_mates_01(self):
        # Initialise myself
        state: PlayerState = PlayerState()
        state.world_view.side = "l"
        state.team_name = "Team1"
        state.position.set_value(Coordinate(-1.94, -2.54), 0)

        # Set opponents
        op1 = PrecariousData(ObservedPlayer("Team2", 1, 4.47, 45, 0, 0, 0, 0, False, Coordinate(2.06, -4.54)), 0)
        op2 = PrecariousData(ObservedPlayer("Team2", 2, 5.55, -45, 0, 0, 0, 0, False, Coordinate(2.2, 1.15)), 0)
        state.world_view.other_players.append(op1)
        state.world_view.other_players.append(op2)

        # Set team_mate who is offside
        tm = PrecariousData(ObservedPlayer("Team1", 2, 6.08, 0, 0, 0, 0, 0, False, Coordinate(4.06, -1.54)), 0)
        state.world_view.other_players.append(tm)

        non_offside_team_mates = state.world_view.get_non_offside_forward_team_mates("Team1"
                                                                                     , state.world_view.side
                                                                                     , state.position.get_value()
                                                                                     , max_data_age=1
                                                                                     , min_distance_free=2
                                                                                     , min_dist_from_me=1)

        self.assertEqual(len(non_offside_team_mates), 0, "In this scenario, there should be no free non-offside players")

    # LEFT SIDE
    def test_get_non_offside_forward_team_mates_02(self):
        # Initialise myself
        state: PlayerState = PlayerState()
        state.world_view.side = "l"
        state.team_name = "Team1"
        state.position.set_value(Coordinate(-1.94, -2.54), 0)

        # Set opponents
        op1 = PrecariousData(ObservedPlayer("Team2", 1, 4.47, 45, 0, 0, 0, 0, False, Coordinate(2.06, -4.54)), 0)
        op2 = PrecariousData(ObservedPlayer("Team2", 2, 9.63, -45, 0, 0, 0, 0, False, Coordinate(6.4, 2.27)), 0)
        state.world_view.other_players.append(op1)
        state.world_view.other_players.append(op2)

        # Set team_mate who is offside
        tm = PrecariousData(ObservedPlayer("Team1", 2, 6.08, 0, 0, 0, 0, 0, False, Coordinate(4.06, -1.54)), 0)
        state.world_view.other_players.append(tm)

        non_offside_team_mates = state.world_view.get_non_offside_forward_team_mates("Team1"
                                                                                     , state.world_view.side
                                                                                     , state.position.get_value()
                                                                                     , max_data_age=1
                                                                                     , min_distance_free=2
                                                                                     , min_dist_from_me=1)

        non_off_side_player: [ObservedPlayer] = non_offside_team_mates[0]

        self.assertEqual(non_off_side_player.num, 2, "Assert that the correct player is found")
        self.assertEqual(len(non_offside_team_mates), 1, "In this scenario, there should be 1 non-offside player")

    # RIGHT SIDE
    def test_get_non_offside_forward_team_mates_03(self):
        # Initialise myself
        state: PlayerState = PlayerState()
        state.world_view.side = "r"
        state.team_name = "Team1"
        state.position.set_value(Coordinate(1.94, -2.54), 0)

        # Set opponents
        op1 = PrecariousData(ObservedPlayer("Team2", 1, 4.47, 45, 0, 0, 0, 0, False, Coordinate(-2.06, -4.54)), 0)
        op2 = PrecariousData(ObservedPlayer("Team2", 2, 5.55, -45, 0, 0, 0, 0, False, Coordinate(-2.2, 1.15)), 0)
        state.world_view.other_players.append(op1)
        state.world_view.other_players.append(op2)

        # Set team_mate who is offside
        tm = PrecariousData(ObservedPlayer("Team1", 2, 6.08, 0, 0, 0, 0, 0, False, Coordinate(-4.06, -1.54)), 0)
        state.world_view.other_players.append(tm)

        non_offside_team_mates = state.world_view.get_non_offside_forward_team_mates("Team1"
                                                                                     , state.world_view.side
                                                                                     , state.position.get_value()
                                                                                     , max_data_age=1
                                                                                     , min_distance_free=2
                                                                                     , min_dist_from_me=1)

        self.assertEqual(len(non_offside_team_mates), 0, "In this scenario, there should be no free non-offside players")

    # RIGHT SIDE
    def test_get_non_offside_forward_team_mates_04(self):
        # Initialise myself
        state: PlayerState = PlayerState()
        state.world_view.side = "r"
        state.team_name = "Team1"
        state.position.set_value(Coordinate(1.94, -2.54), 0)

        # Set opponents
        op1 = PrecariousData(ObservedPlayer("Team2", 1, 4.47, 45, 0, 0, 0, 0, False, Coordinate(-2.06, -4.54)), 0)
        op2 = PrecariousData(ObservedPlayer("Team2", 2, 9.63, -45, 0, 0, 0, 0, False, Coordinate(-6.4, 2.27)), 0)
        state.world_view.other_players.append(op1)
        state.world_view.other_players.append(op2)

        # Set team_mate who is offside
        tm = PrecariousData(ObservedPlayer("Team1", 2, 6.08, 0, 0, 0, 0, 0, False, Coordinate(-4.06, -1.54)), 0)
        state.world_view.other_players.append(tm)

        non_offside_team_mates = state.world_view.get_non_offside_forward_team_mates("Team1"
                                                                                     , state.world_view.side
                                                                                     , state.position.get_value()
                                                                                     , max_data_age=1
                                                                                     , min_distance_free=2
                                                                                     , min_dist_from_me=1)

        non_off_side_player: [ObservedPlayer] = non_offside_team_mates[0]

        self.assertEqual(non_off_side_player.num, 2, "Assert that the correct player is found")
        self.assertEqual(len(non_offside_team_mates), 1, "In this scenario, there should be 1 non-offside player")

    # LEFT SIDE on own side, should never be offside
    def test_get_non_offside_forward_team_mates_05(self):
        # Initialise myself
        state: PlayerState = PlayerState()
        state.world_view.side = "l"
        state.team_name = "Team1"
        state.position.set_value(Coordinate(-11.83, -6), 0)

        # Set opponents
        op1 = PrecariousData(ObservedPlayer("Team2", 1, 4.47, 45, 0, 0, 0, 0, False, Coordinate(-7.83, -8)), 0)
        op2 = PrecariousData(ObservedPlayer("Team2", 2, 5.55, -45, 0, 0, 0, 0, False, Coordinate(-7.7, -2.31)), 0)
        state.world_view.other_players.append(op1)
        state.world_view.other_players.append(op2)

        # Set team_mate who is offside
        tm = PrecariousData(ObservedPlayer("Team1", 2, 6.08, 0, 0, 0, 0, 0, False, Coordinate(-5.83, -5)), 0)
        state.world_view.other_players.append(tm)

        non_offside_team_mates = state.world_view.get_non_offside_forward_team_mates("Team1"
                                                                                     , state.world_view.side
                                                                                     , state.position.get_value()
                                                                                     , max_data_age=1
                                                                                     , min_distance_free=2
                                                                                     , min_dist_from_me=1)

        non_off_side_player: [ObservedPlayer] = non_offside_team_mates[0]

        self.assertEqual(non_off_side_player.num, 2, "Assert that the correct player is found")
        self.assertEqual(len(non_offside_team_mates), 1, "In this scenario, there should be 1 non-offside player")


    # RIGHT SIDE on own side, should never be offside
    def test_get_non_offside_forward_team_mates_06(self):
        # Initialise myself
        state: PlayerState = PlayerState()
        state.world_view.side = "r"
        state.team_name = "Team1"
        state.position.set_value(Coordinate(11.83, -6), 0)

        # Set opponents
        op1 = PrecariousData(ObservedPlayer("Team2", 1, 4.47, 45, 0, 0, 0, 0, False, Coordinate(7.83, -8)), 0)
        op2 = PrecariousData(ObservedPlayer("Team2", 2, 5.55, -45, 0, 0, 0, 0, False, Coordinate(7.7, -2.31)), 0)
        state.world_view.other_players.append(op1)
        state.world_view.other_players.append(op2)

        # Set team_mate who is offside
        tm = PrecariousData(ObservedPlayer("Team1", 2, 6.08, 0, 0, 0, 0, 0, False, Coordinate(5.83, -5)), 0)
        state.world_view.other_players.append(tm)

        non_offside_team_mates = state.world_view.get_non_offside_forward_team_mates("Team1"
                                                                                     , state.world_view.side
                                                                                     , state.position.get_value()
                                                                                     , max_data_age=1
                                                                                     , min_distance_free=2
                                                                                     , min_dist_from_me=1)

        non_off_side_player: [ObservedPlayer] = non_offside_team_mates[0]

        self.assertEqual(non_off_side_player.num, 2, "Assert that the correct player is found")
        self.assertEqual(len(non_offside_team_mates), 1, "In this scenario, there should be 1 non-offside player")