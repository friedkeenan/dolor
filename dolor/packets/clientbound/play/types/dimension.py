from ..... import nbt
from .....types import *

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

DimensionCodec = NBT.Compound("DimensionCodec",
    {
        # Marked optional since the client doesn't
        # explicitly error if it's missing
        "minecraft:dimension_type": NBT.Optional(NBT.Compound("DimensionType",
            type  = NBT.Identifier,
            value = NBT.List(NBT.Compound("DimensionDescriptor",
                name    = NBT.Identifier,
                id      = nbt.Int,
                element = Dimension,
            )),
        )),

        # Marked optional for same reasons as above
        "minecraft:worldgen/biome": NBT.Optional(NBT.Compound("Biomes",
            type  = NBT.Identifier,
            value = NBT.List(NBT.Compound("BiomeDescriptor",
                name    = NBT.Identifier,
                id      = nbt.Int,
                element = Biome,
            )),
        )),
    },
)
