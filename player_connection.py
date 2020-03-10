import re
import select
import socket


class PlayerConnection:

    def __init__(self, UDP_IP, UDP_PORT) -> None:
        self.addr = (UDP_IP, UDP_PORT)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setblocking(False)

    def connect_to_server(self, player_state):
        self.send_message("(init " + player_state.team_name + ")")

        msg_received = self.receive_message()  # buffer size is 1024 bytes
        regex = re.compile("\\(init ([lr]) ([0-9]*)")
        match = regex.match(msg_received.__str__())
        player_state.side = match.group(1)
        player_state.player_num = match.group(2)

    def send_message(self, msg: str):
        bytes_to_send = str.encode(msg)
        self.sock.sendto(bytes_to_send, self.addr)

    def receive_message(self):
        ready = select.select([self.sock], [], [], 0.02)
        if ready[0]:
            player_info = self.sock.recv(1024)
            return player_info.decode()

        return None
