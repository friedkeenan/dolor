from .... import enums
from .... import nbt
from ....types import *
from ...packet import *

class Base(ClientboundPacket, PlayPacket):
    pass

GameMode = Enum(UnsignedByte, enums.GameMode)

Dimension = NBT.Compound("Dimension",
    ambient_light    = nbt.Float,
    logical_height   = nbt.Int,
    coordinate_scale = nbt.Double,
    fixed_time       = NBT.Optional(nbt.Long),
    infiniburn       = NBT.Identifier,
    effects          = NBT.Identifier,

    piglin_safe          = NBT.Boolean,
    natural              = NBT.Boolean,
    respawn_anchor_works = NBT.Boolean,
    has_skylight         = NBT.Boolean,
    bed_works            = NBT.Boolean,
    has_raids            = NBT.Boolean,
    ultrawarm            = NBT.Boolean,
    has_ceiling          = NBT.Boolean,
)

DimensionCodec = NBT.Compound("DimensionCodec",
    {
        "minecraft:dimension_type": NBT.Optional(NBT.Compound("DimensionType",
            type  = NBT.Identifier,
            value = NBT.List(NBT.Compound("DimensionDescriptor",
                name    = NBT.Identifier,
                id      = nbt.Int,
                element = Dimension,
            )),
        )),

        # TODO: Fill this out
        "minecraft:worldgen/biome": NBT.Optional(nbt.Compound),
    },
)

class ChatMessagePacket(Base):
    id = 0x0e

    data:     Chat
    position: Enum(Byte, enums.ChatPosition)
    sender:   UUID

class DisconnectPlayPacket(Base):
    id = 0x19

    reason: Chat

class KeepAlivePacket(Base):
    id = 0x1f

    keep_alive_id: Long

class JoinGamePacket(Base):
    id = 0x24

    entity_id:             Int
    hardcore:              Boolean
    game_mode:             GameMode
    prev_game_mode:        GameMode
    world_names:           Identifier[VarInt]
    dimension_codec:       DimensionCodec
    dimension:             Dimension
    world_name:            Identifier
    hashed_seed:           Long
    max_players:           VarInt
    view_distance:         VarInt
    reduced_debug_info:    Boolean
    enable_respawn_screen: Boolean
    debug:                 Boolean
    flat:                  Boolean

class PlayerPositionAndLook(Base):
    id = 0x34

    position: Vector(Double)
    yaw:      Float
    pitch:    Float

    relative: BitFlag(UnsignedByte,
        x     = 0,
        y     = 1,
        z     = 2,
        y_rot = 3,
        x_rot = 4,
    )

    teleport_id: VarInt

class RespawnPacket(Base):
    id = 0x39

    dimension:      Dimension
    world_name:     Identifier
    hashed_seed:    Long
    game_mode:      GameMode
    prev_game_mode: GameMode
    debug:          Boolean
    flat:           Boolean
    copy_metadata:  Boolean

class UpdateHealthPacket(Base):
    id = 0x49

    health:     Float
    food:       VarInt
    saturation: Float
