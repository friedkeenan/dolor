from .... import enums
from .... import nbt
from ....versions import VersionRange
from ....types import *
from ...packet import *

GameMode = Enum(UnsignedByte, enums.GameMode)

DimensionCompound = NBT.Compound("DimensionCompound",
    ambient_light    = nbt.Float,
    logical_height   = nbt.Int,
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

    name = {
        VersionRange(None, "20w28a"): NBT.Identifier,
        VersionRange("20w28a", None): None,
    },

    shrunk = {
        VersionRange(None, "20w28a"): NBT.Boolean,
        VersionRange("20w28a", None): None,
    },

    coordinate_scale = {
        VersionRange(None, "20w28a"): None,
        VersionRange("20w28a", None): nbt.Double,
    },
)

Biome = NBT.Compound("Biome",
    category      = nbt.String,
    precipitation = nbt.String,
    downfall      = nbt.Float,
    temperature   = nbt.Float,
    depth         = nbt.Float,
    scale         = nbt.Float,

    effects = NBT.Compound("BiomeEffects",
        # TODO: NBT.Color specialization?
        sky_color       = nbt.Int,
        fog_color       = nbt.Int,
        water_color     = nbt.Int,
        water_fog_color = nbt.Int,

        mood_sound = NBT.Compound("Sound",
            sound               = NBT.Identifier,
            offset              = nbt.Double,
            tick_delay          = nbt.Int,
            block_search_extent = nbt.Int,
        ),
    ),
)

DimensionCodec = NBT.Compound("DimensionCodec", {
    "minecraft:dimension_type": {
        VersionRange(None, "20w28a"): None,

        # Marked optional since the client doesn't
        # explicitly error if it's missing
        VersionRange("20w28a", None): NBT.Optional(NBT.Compound("DimensionType",
            type  = NBT.Identifier,
            value = NBT.List(NBT.Compound("DimensionDescriptor",
                name    = NBT.Identifier,
                id      = nbt.Int,
                element = DimensionCompound,
            )),
        )),
    },

    "minecraft:worldgen/biome": {
        VersionRange(None, "20w28a"): None,

        # Marked optional for same reasons as above
        VersionRange("20w28a", None): NBT.Optional(NBT.Compound("Biomes",
            type  = NBT.Identifier,
            value = NBT.List(NBT.Compound("BiomeDescriptor",
                name    = NBT.Identifier,
                id      = nbt.Int,
                element = Biome,
            )),
        )),
    },

    "dimension": {
        VersionRange(None, "1.16-pre3"): NBT.List(NBT.Compound("DimensionItem",
            key     = NBT.Identifier,
            element = NBT.Identifier,
        )),

        VersionRange("1.16-pre3", "20w28a"): NBT.List(DimensionCompound),
        VersionRange("20w28a", None):        None,
    },
})

Dimension = {
    VersionRange(None, "20w21a"):          Enum(Int, enums.LegacyDimension),
    VersionRange("20w21a", "1.16.2-pre3"): Identifier,
    VersionRange("1.16.2-pre3", None):     DimensionCompound,
}

class JoinGamePacket(ClientboundPacket, PlayPacket):
    id = {
        VersionRange(None, "1.16-pre1"):     0x26,
        VersionRange("1.16-pre1", "20w28a"): 0x25,
        VersionRange("20w28a", None):        0x24,
    }

    entity_id: Int

    hardcore: {
        VersionRange(None, "20w27a"): None,
        VersionRange("20w27a", None): Boolean,
    }

    game_mode: GameMode

    prev_game_mode: {
        VersionRange(None, "1.16-pre6"): None,
        VersionRange("1.16-pre6", None): GameMode,
    }

    world_names: {
        VersionRange(None, "20w22a"): None,
        VersionRange("20w22a", None): Identifier[VarInt]
    }

    dimension_codec: {
        VersionRange(None, "20w21a"): None,
        VersionRange("20w21a", None): DimensionCodec,
    }

    dimension: Dimension

    world_name: {
        VersionRange(None, "20w22a"): None,
        VersionRange("20w22a", None): Identifier,
    }

    hashed_seed: Long
    max_players: VarInt

    level_type: {
        VersionRange(None, "20w20a"): Enum(String(16), enums.LevelType),
        VersionRange("20w20a", None): None,
    }

    view_distance:         VarInt
    reduced_debug_info:    Boolean
    enable_respawn_screen: Boolean

    debug: {
        VersionRange(None, "20w20a"): None,
        VersionRange("20w20a", None): Boolean,
    }

    flat: {
        VersionRange(None, "20w20a"): None,
        VersionRange("20w20a", None): Boolean,
    }

class RespawnPacket(ClientboundPacket, PlayPacket):
    id = {
        VersionRange(None, "1.16-pre1"):     0x3b,
        VersionRange("1.16-pre1", "20w28a"): 0x3a,
        VersionRange("20w28a", None):        0x39,
    }

    dimension: Dimension

    world_name: {
        VersionRange(None, "20w22a"): None,
        VersionRange("20w22a", None): Identifier,
    }

    hashed_seed: Long
    game_mode:   GameMode

    prev_game_mode: {
        VersionRange(None, "1.16-pre6"): None,
        VersionRange("1.16-pre6", None): GameMode,
    }

    level_type: {
        VersionRange(None, "20w20a"): Enum(String(16), enums.LevelType),
        VersionRange("20w20a", None): None,
    }

    debug: {
        VersionRange(None, "20w20a"): None,
        VersionRange("20w20a", None): Boolean,
    }

    flat: {
        VersionRange(None, "20w20a"): None,
        VersionRange("20w20a", None): Boolean,
    }

    copy_metadata: {
        VersionRange(None, "20w18a"): None,
        VersionRange("20w18a", None): Boolean,
    }

