import socket
import client
import threading

TEAM_NAME = "PhilipsTeam2"
NUM_PLAYERS = 11

clients = []

UDP_IP = "127.0.0.1"
UDP_PORT = 6000

for i in range(0, NUM_PLAYERS):
    print i
    clients.append(threading.Thread(target=lambda: client.Client(TEAM_NAME).connect_to_server(UDP_PORT, UDP_IP)))

for thread in clients:
    thread.start()


