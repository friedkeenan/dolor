import enum

from . import util

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

    # Hardcore flag is bit 3, only used on older versions
    HardcoreSurvival  = util.bit(3) | Survival
    HardcoreCreative  = util.bit(3) | Creative
    HardcoreAdventure = util.bit(3) | Adventure
    HardcoreSpectator = util.bit(3) | Spectator

    Invalid = 255

class LegacyDimension(enum.Enum):
    Overworld =  0
    Nether    = -1
    End       =  1

class LevelType(enum.Enum):
    Default     = "default"
    Flat        = "flat"
    LargeBiomes = "largeBiomes"
    Amplified   = "amplified"
    Customized  = "customized"
    Buffet      = "buffet"
    Default_1_1 = "defalt_1_1"
