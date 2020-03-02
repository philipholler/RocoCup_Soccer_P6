import socket
import client
import threading

TEAM_NAMES = ["Team1", "Team2"]
NUM_PLAYERS = 11

clients = []

UDP_IP = "127.0.0.1"
UDP_PORT = 6000

for team in TEAM_NAMES:
    for player in range(0, NUM_PLAYERS):
        clients.append(threading.Thread(target=client.Client, args=(team, UDP_PORT, UDP_IP)))
        # clients.append(threading.Thread(target=lambda: client.Client(team,).connect_to_server(UDP_PORT, UDP_IP)))

for thread in clients:
    thread.start()
