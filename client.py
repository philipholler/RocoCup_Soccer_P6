import socket
import re


class Client:
    BUFFER_SIZE = 1024

    # default constructor
    def __init__(self, team_name, port, ip):
        self.side = ""
        self.player_num = ""
        self.team_name = team_name
        self.port = ""
        self.server_ip = ""
        self.client_socket = ""

        self.connect_to_server(port, ip)

    def connect_to_server(self, port: str, ip: str):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.port = port
        self.server_ip = ip

        self.send_message("(init " + self.team_name + ")")

        player_info = self.receive_message()  # buffer size is 1024 bytes
        regex = re.compile("\\(init ([lr]) ([0-9]*)")
        match = regex.match(player_info.__str__())
        self.side = match.group(1)
        self.player_num = match.group(2)

        # print("New player, team_name: ", self.team_name, " player_num: ", self.player_num, "\n")

        # Move to a position
        self.send_message("(move -10 -10)")

        while True:
            data = self.receive_message()  # buffer size is 1024 bytes
            if self.player_num == "1" and self.team_name == "Team1":
                self.send_message("(dash -5)")
                print("Received message:", data.__str__())

    def send_message(self, msg: str):
        bytes_to_send = str.encode(msg)
        self.client_socket.sendto(bytes_to_send, (self.server_ip, self.port))

    def receive_message(self):
        player_info = self.client_socket.recv(self.BUFFER_SIZE).decode()
        return player_info

