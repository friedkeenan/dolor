import enum

class State(enum.Enum):
    Handshaking = 0
    Status      = 1
    Login       = 2
    Play        = 3

class ChatPosition(enum.Enum):
    Chat     = 0
    System   = 1
    GameInfo = 2

class Action(enum.Enum):
    Respawn      = 0
    RequestStats = 1

class GameMode(enum.Enum):
    Survival  = 0
    Creative  = 1
    Adventure = 2
    Spectator = 3

    Invalid = 255
