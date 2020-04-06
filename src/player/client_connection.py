import select
import socket
import threading
import queue
from player.coach.coachThinker import CoachThinker


class Connection(threading.Thread):

    def __init__(self, UDP_IP, UDP_PORT, think):
        super().__init__()
        self._stop_event = threading.Event()
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
                if self._stop_event.is_set():
                    return
                msg = self._receive_message()
                if msg is None:
                    break
                self.think.input_queue.put(msg)
            while not self.action_queue.empty():
                if self._stop_event.is_set():
                    return
                self._send_message(self.action_queue.get())
            if self._stop_event.is_set():
                return

    def stop(self) -> None:
        self._stop_event.set()
        self._send_bye()

    def _send_bye(self):
        self._send_message("(bye)")

    def _send_message(self, msg: str):
        # \0 is the string terminator for C++
        bytes_to_send = (msg + "\0").encode("utf-8")
        self.sock.sendto(bytes_to_send, self.addr)

    def _receive_message(self):
        ready = select.select([self.sock], [], [], 0.02)
        if ready[0]:
            player_info, address = self.sock.recvfrom(1024)
            # The client will be sent the init ok message from a different port.
            # Adapt socket to this port. Each client gets it's own port like this.
            if self.addr != address:
                self.addr = address
            return player_info.decode()
        return None