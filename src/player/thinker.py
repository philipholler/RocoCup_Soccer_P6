import enum
import threading
import queue

from geometry import calculate_origin_angle_between
from player import player_connection, player
import time
import parsing
import random as r
import player.strategy as strategy
from player.world import Coordinate


class Thinker(threading.Thread):
    def __init__(self, team_name: str):
        super().__init__()
        self.player_state = player.PlayerState()
        self.player_state.team_name = team_name
        # Connection with the server
        self.player_conn: player_connection.PlayerConnection = None
        # Queue for actions to be send
        self.action_queue = queue.Queue()
        # Non processed inputs from server
        self.input_queue = queue.Queue()
        self.current_objective: Objective = None

        self.strategy = strategy.Strategy(self.player_state)

        self.my_bool = True

    def start(self) -> None:
        super().start()
        init_string = "(init " + self.player_state.team_name + ")"
        self.player_conn.action_queue.put(init_string)
        self.position_player()

    def run(self) -> None:
        super().run()
        while True:
            self.think()

    def think(self):
        time.sleep(0.1)
        while not self.input_queue.empty():
            # Parse message and update player state / world view
            msg = self.input_queue.get()
            parsing.parse_message_update_state(msg, self.player_state)
            # Give the strategy a new state
            self.strategy.player_state = self.player_state

        # Update current objective in accordance to the player's strategy
        self.current_objective = self.strategy.determine_objective(self.player_state, self)
        self.current_objective.perform_action()
        return

    def position_player(self):
        x = r.randint(-20, 20)
        y = r.randint(-20, 20)
        move_action = "(move " + str(x) + " " + str(y) + ")"
        self.player_conn.action_queue.put(move_action)

    def jog_towards(self, target_position: Coordinate):
        if not self.player_state.position.is_value_known() or self.player_state.player_angle.is_value_known():
            self.orient_self()

        # delta angle should depend on how close the player is to the target
        if not self.player_state.facing(target_position, 5):
            rotation = calculate_origin_angle_between(self.player_state.position.get_value(), target_position)
            rotation -= self.player_state.player_angle.get_value()
            self.player_conn.action_queue.put("(turn %i)".format(rotation))
        else:
            pass

    def is_near(self, coordinate: Coordinate):
        if not self.player_state.position.is_value_known():
            return False

        # temporary value
        allowed_delta = 2.0

        distance = coordinate.euclidean_distance_from(self.player_state.position.get_value())
        return distance < allowed_delta

    def orient_self(self):
        pass


class Objective:

    def __init__(self, action_to_perform, achievement_criteria) -> None:
        self.achievement_criteria = achievement_criteria
        self.perform_action = action_to_perform

    def is_achieved(self):
        return self.achievement_criteria()

    def perform_action(self):
        self.perform_action()
