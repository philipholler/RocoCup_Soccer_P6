import select
import socket
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
                msg = self.__receive_message()
                if msg is None:
                    break
                self.think.input_queue.put(msg)
            while not self.action_queue.empty():
                self.__send_message(self.action_queue.get())

    def __send_message(self, msg: str):
        bytes_to_send = str.encode(msg)
        self.sock.sendto(bytes_to_send, self.addr)

    def __receive_message(self):
        ready = select.select([self.sock], [], [], 0.02)
        if ready[0]:
            player_info = self.sock.recv(1024)
            return player_info.decode()
        return None
