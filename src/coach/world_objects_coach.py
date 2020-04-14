from player.world_objects import Coordinate


class PlayerViewCoach:
    def __init__(self, team, num, is_goalie, coord, delta_x, delta_y, body_angle, neck_angle, has_ball) -> None:
        super().__init__()
        self.team = team
        self.num = num
        self.is_goalie = is_goalie
        self.coord: Coordinate = coord
        self.has_ball: bool = has_ball
        self.delta_x = 0
        self.delta_y = 0
        self.body_angle = body_angle
        self.neck_angle = neck_angle

    def __repr__(self) -> str:
        return "(team: {0}, num: {1}, is_goalie: {2}, coord: {3}, delta_x: {4}, delta_y: {5}, body_angle: {6}, " \
               "neck_angle: {7}, has_ball: {8})".format(self.team, self.num, self.is_goalie, self.coord
                                         , self.delta_x, self.delta_y, self.body_angle
                                         , self.neck_angle, self.has_ball)


def distance_to_ball(play: PlayerViewCoach, ball: Coordinate):
    return play.coord.euclidean_distance_from(ball)


class WorldViewCoach:
    def __init__(self, sim_time, team_name):
        self.sim_time = sim_time
        self.team = team_name
        self.players: [PlayerViewCoach] = []
        self.ball: BallOnlineCoach = None
        self.goals = []
        self.lines = []
        self.side = ""
        self.game_state = ""

    def __repr__(self) -> str:
        return super().__repr__()

    def get_closest_team_players_to_ball(self, amount) -> [PlayerViewCoach]:
        # Get only players from same team
        same_team_players: [PlayerViewCoach] = filter(lambda x: (x.team == self.team), self.players)
        # Sort by distance to ball
        sorted_list: [PlayerViewCoach] = sorted(same_team_players, key=lambda play: distance_to_ball(play, self.ball.coord))
        # Return only the first *amount* of players
        return sorted_list[:amount]

    def get_closest_players_to_ball(self, amount) -> [PlayerViewCoach]:
        # Sort by distance to ball
        sorted_list: [PlayerViewCoach] = sorted(self.players, key=lambda play: distance_to_ball(play, self.ball.coord))
        # Return only the first *amount* of players
        return sorted_list[:amount]


class BallOnlineCoach:
    def __init__(self, coord, delta_x, delta_y) -> None:
        super().__init__()
        self.coord = coord
        self.delta_x = delta_x
        self.delta_y = delta_y

    def __repr__(self) -> str:
        return "(Coord: {0}, delta_x: {1}, delta_y: {2})".format(self.coord, self.delta_x, self.delta_y)



