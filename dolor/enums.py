from enum import Enum

class State(Enum):
    Handshaking = 0
    Status      = 1
    Login       = 2
    Play        = 3

class Dimension(Enum):
    Nether    = -1
    Overworld =  0
    ENd       =  1

class Action(Enum):
    Respawn      = 0
    RequestStats = 1

class ChatPosition(Enum):
    Chat     = 0
    System   = 1
    GameInfo = 2