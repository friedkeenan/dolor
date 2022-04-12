"""Miscellaneous enums for Minecraft."""

import enum
import pak

class ChatPosition(enum.Enum):
    """The position of a :class:`clientbound.ChatMessagePacket <.clientbound.play.misc.ChatMessagePacket>`."""

    Chat     = 0
    System   = 1
    GameInfo = 2

class GameMode(enum.Enum):
    """The game mode of a player."""

    Survival  = 0
    Creative  = 1
    Adventure = 2
    Spectator = 3

    HardcoreSurvival  = pak.util.bit(3) | Survival
    HardcoreCreative  = pak.util.bit(3) | Creative
    HardcoreAdventure = pak.util.bit(3) | Adventure
    HardcoreSpectator = pak.util.bit(3) | Spectator

    def is_gamemode(self, mode):
        return (self.value & 0b11) == mode.value

    @property
    def is_hardcore(self):
        return (self.value & pak.util.bit(3)) != 0

class Dimension(enum.Enum):
    """A dimension within a world."""

    Nether    = -1
    Overworld = 0
    End       = 1

class Difficulty(enum.Enum):
    """The difficulty setting of Minecraft."""

    Peaceful = 0
    Easy     = 1
    Normal   = 2
    Hard     = 3

class LevelType(enum.Enum):
    """The type of generation of a world."""

    Default     = "default"
    Flat        = "flat"
    LargeBiomes = "largeBiomes"
    Amplified   = "amplified"
    Default_1_1 = "default_1_1"
