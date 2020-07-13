from enum import Enum

class State(Enum):
    Handshaking = 0
    Status      = 1
    Login       = 2
    Play        = 3