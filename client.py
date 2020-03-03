import socket
import re


class Client:

    # default constructor
    def __init__(self, team_name, port, ip):
        self.side = ""
        self.player_num = ""
        self.team_name = team_name
        self.port = ""
        self.server_ip = ""
        self.sock = ""

        self.connect_to_server(port, ip)

    def connect_to_server(self, port: str, ip: str):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.port = port
        self.server_ip = ip

        self.send_message("(init " + self.team_name + ")")

        player_info, addr = self.sock.recvfrom(1024)  # buffer size is 1024 bytes
        # print("Received message:", player_info)
        regex = re.compile("b'\\(init ([lr]) ([0-9]*)")
        match = regex.match(player_info.__str__())
        # print("Side: ", match.group(1))
        # print("Player_num", match.group(2))
        self.side = match.group(1)
        self.player_num = match.group(2)

        # print("New player, team_name: ", self.team_name, " player_num: ", self.player_num, "\n")

        # Move to a position
        self.send_message("(move -10 -10)")

        while True:
            data, addr = self.sock.recvfrom(1024)  # buffer size is 1024 bytes
            self.send_message("(dash 20)")
            if self.player_num == "1" and self.team_name == "Team1":
                print("Received message:", data.__str__())
            # print("Received message:", data.__str__())

    def send_message(self, msg: str):
        bytes_to_send = str.encode(msg)
        self.sock.sendto(bytes_to_send, (self.server_ip, self.port))
