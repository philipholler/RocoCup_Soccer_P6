from unittest import TestCase

from coaches.world_objects_coach import WorldViewCoach, PlayerViewCoach, BallOnlineCoach
from player.world_objects import Coordinate


class TestWorldViewCoach(TestCase):
    def test_get_closest_team_players_to_ball_00(self):
        wv = WorldViewCoach(0, "Team1")
        player1 = PlayerViewCoach("Team1", 1, False, Coordinate(10, 10), 0, 0, 0, 0, False)
        player2 = PlayerViewCoach("Team1", 2, False, Coordinate(5, 5), 0, 0, 0, 0, False)
        player3 = PlayerViewCoach("Team1", 3, False, Coordinate(0, 0), 0, 0, 0, 0, False)
        wv.players.append(player1)
        wv.players.append(player3)
        wv.players.append(player2)
        wv.ball = BallOnlineCoach(Coordinate(0, 0), 0, 0)

        result: [PlayerViewCoach] = wv.get_closest_team_players_to_ball(3)
        self.assertEqual(len(result), 3, "Amount of results should fit the argument.")
        self.assertEqual(result[0].num, 3, "Player 3 should be the closest")
        self.assertEqual(result[1].num, 2, "Player 2 should be second closest")
        self.assertEqual(result[2].num, 1, "Player 1 should be furthest away")

    def test_get_closest_team_players_to_ball_01(self):
        wv = WorldViewCoach(0, "Team1")
        player1 = PlayerViewCoach("Team1", 1, False, Coordinate(10, 10), 0, 0, 0, 0, False)
        player2 = PlayerViewCoach("Team1", 2, False, Coordinate(5, 5), 0, 0, 0, 0, False)
        player3 = PlayerViewCoach("Team1", 3, False, Coordinate(100, 100), 0, 0, 0, 0, False)
        wv.players.append(player1)
        wv.players.append(player3)
        wv.players.append(player2)
        wv.ball = BallOnlineCoach(Coordinate(0, 0), 0, 0)

        # take only 2 closest players
        result: [PlayerViewCoach] = wv.get_closest_team_players_to_ball(2)
        self.assertEqual(len(result), 2, "Amount of results should fit the argument.")
        self.assertEqual(result[0].num, 2, "Player 2 should be the closest")
        self.assertEqual(result[1].num, 1, "Player 1 should be second closest")

    def test_get_closest_team_players_to_ball_02(self):
        wv = WorldViewCoach(0, "Team1")
        player1 = PlayerViewCoach("Team1", 1, False, Coordinate(10, 10), 0, 0, 0, 0, False)
        player2 = PlayerViewCoach("Team1", 2, False, Coordinate(5, 5), 0, 0, 0, 0, False)
        player3 = PlayerViewCoach("Team2", 3, False, Coordinate(100, 100), 0, 0, 0, 0, False)

        wv.players.append(player1)
        wv.players.append(player3)
        wv.players.append(player2)
        wv.ball = BallOnlineCoach(Coordinate(0, 0), 0, 0)

        # take only 2 closest players
        result: [PlayerViewCoach] = wv.get_closest_team_players_to_ball(2)
        # Player 3 is team 2, and should not be included
        self.assertEqual(len(result), 2, "Amount of results should fit the argument")
        self.assertEqual(result[0].num, 2, "Player 2 should be the closest")
        self.assertEqual(result[1].num, 1, "Player 1 should be second closest")

    def test_get_closest_team_players_to_ball_03(self):
        wv = WorldViewCoach(0, "Team2")
        player1 = PlayerViewCoach("Team1", 1, False, Coordinate(10, 10), 0, 0, 0, 0, False)
        player2 = PlayerViewCoach("Team1", 2, False, Coordinate(5, 5), 0, 0, 0, 0, False)
        player3 = PlayerViewCoach("Team2", 3, False, Coordinate(100, 100), 0, 0, 0, 0, False)

        wv.players.append(player1)
        wv.players.append(player3)
        wv.players.append(player2)
        wv.ball = BallOnlineCoach(Coordinate(0, 0), 0, 0)

        # take only closest player
        result: [PlayerViewCoach] = wv.get_closest_team_players_to_ball(1)
        # Player 3 is team 2, the rest should not be included
        self.assertEqual(len(result), 1, "Amount of results should fit the argument")
        self.assertEqual(result[0].num, 3, "Player 3 should be the closest")

    def test_get_closest_opponents(self):
        wv = WorldViewCoach(0, "Team1")
        wv.ball = BallOnlineCoach(Coordinate(0, 0), 0, 0)
        for team in ["Team1", "Team2"]:
            for num in range(0, 11):
                posx = (20 - num) if team == "Team1" else num
                wv.players.append(PlayerViewCoach(team, str(num), False, Coordinate(posx, posx), 0, 0, 0, 0, False))

        closest_team_members = wv.get_closest_team_players_to_ball(5)
        closest_opponents = wv.get_closest_opponents(closest_team_members, 5)

        for i in range(0, 5):
            self.assertEqual(10 - i, closest_opponents[i].num)

    def test_get_closest_ordered_opponents(self):
        wv = WorldViewCoach(0, "Team1")
        wv.ball = BallOnlineCoach(Coordinate(0, 0), 0, 0)
        for team in ["Team1", "Team2"]:
            for num in range(0, 11):
                wv.players.append(
                    PlayerViewCoach(team, str(num), False, Coordinate(num, num), 0, 0, 0, 0, False))

        closest_team_members = wv.get_closest_team_players_to_ball(5)
        closest_opponents = wv.get_closest_opponents(closest_team_members, 5)

        for i in range(0, 5):
            self.assertEqual(i, closest_opponents[i].num)



