from geometry import calculate_origin_angle_between
from player.world import PrecariousData, World, Player, Coordinate

MAX_MOVE_DISTANCE_PER_TICK = 2.5  # todo random guess. Look up max_speed in manual


class PlayerState:

    def __init__(self):
        self.side = ""
        self.team_name = ""
        self.player_num = -1
        self.game_state = ""
        self.position: PrecariousData = PrecariousData.unknown()
        self.world_view = WorldView(0)
        self.player_angle: PrecariousData = PrecariousData.unknown()
        super().__init__()

    def __str__(self) -> str:
        return "side: {0}, team_name: {1}, player_num: {2}".format(self.side, self.team_name, self.player_num)

    def facing(self, coordinate, delta):
        if not self.player_angle.is_value_known() or not self.position.is_value_known():
            # should this return unknown?(None?)
            return False

        expected_angle = calculate_origin_angle_between(self.position.get_value(), coordinate)
        return abs(expected_angle - self.player_angle.get_value()) < delta

    def is_near(self, coordinate: Coordinate):
        if not self.position.is_value_known():
            return False

        # temporary value
        allowed_delta = 2.0

        distance = coordinate.euclidean_distance_from(self.position.get_value())
        return distance < allowed_delta


class WorldView:
    def __init__(self, sim_time):
        self.sim_time = sim_time
        self.other_players = [Player]
        self.ball: PrecariousData = PrecariousData.unknown()
        self.goals = []
        self.lines = []
