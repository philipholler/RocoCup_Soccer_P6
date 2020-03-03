import socket
import client
import threading
import os
import time

TEAM_NAMES = ["Team1", "Team2"]
NUM_PLAYERS = 11

clients = []

UDP_IP = "127.0.0.1"
UDP_PORT = 6000

soccer_sim = threading.Thread(target=lambda: os.system("rcsoccersim")).start()

time.sleep(5)

for team in TEAM_NAMES:
    for player in range(0, NUM_PLAYERS):
        thread = threading.Thread(target=client.Client, args=(team, UDP_PORT, UDP_IP))
        clients.append(thread)
        thread.start()