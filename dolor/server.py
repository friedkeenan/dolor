import socket
from .packets import *

class Server:
    def __init__(self, address=("localhost", 25565)):
        self.sock = socket.socket()
        self.sock.bind(address)
        self.sock.listen(5)

        self.connections = []