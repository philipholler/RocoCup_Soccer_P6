import re
import select
import socket
import player_state
import threading
import thinker
import queue


class PlayerConnection(threading.Thread):

    def __init__(self, UDP_IP, UDP_PORT, think: thinker.Thinker):
        super().__init__()
        self.addr = (UDP_IP, UDP_PORT)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setblocking(False)
        self.think = think
        self.player_conn = None
        self.connected = False
        self.action_queue = queue.Queue()

    def start(self):
        super().start()

    def run(self):
        super().run()
        while True:
            while True:
                msg = self.receive_message()
                if msg is None:
                    break
                self.think.input_queue.put(msg)

            while self.action_queue.not_empty:
                for msg in self.action_queue.get():
                    self.send_message(msg)

    def send_message(self, msg: str):
        bytes_to_send = str.encode(msg)
        self.sock.sendto(bytes_to_send, self.addr)

    def receive_message(self):
        ready = select.select([self.sock], [], [], 0.02)
        if ready[0]:
            player_info = self.sock.recv(1024)
            return player_info.decode()
        return None
