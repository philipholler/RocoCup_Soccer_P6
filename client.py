import socket
import re


class Client:

    # default constructor
    def __init__(self, team_name):
        self.side = ""
        self.player_num = ""
        self.team_name = team_name

    def connect_to_server(self, port, ip):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto("(init " + self.team_name + ")", (ip, port))
        player_info, addr = sock.recvfrom(1024)  # buffer size is 1024 bytes
        print "Received message:", player_info
        regex = re.compile("\\(init ([lr]) ([0-9]*)")
        match = regex.match(player_info)
        self.side = match.group(1)
        self.player_num = match.group(2)
        print(self.side)
        print(self.player_num)

        sock.sendto("(move 10 10)", (ip, port))

        while True:
            data, addr = sock.recvfrom(1024)  # buffer size is 1024 bytes
            print "Received message:", data
