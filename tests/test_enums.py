from dolor import *

def test_gamemode():
    assert enums.GameMode.Survival.is_gamemode(enums.GameMode.Survival)
    assert enums.GameMode.HardcoreSurvival.is_gamemode(enums.GameMode.Survival)

    assert enums.GameMode.Creative.is_gamemode(enums.GameMode.Creative)
    assert enums.GameMode.HardcoreCreative.is_gamemode(enums.GameMode.Creative)

    assert enums.GameMode.Adventure.is_gamemode(enums.GameMode.Adventure)
    assert enums.GameMode.HardcoreAdventure.is_gamemode(enums.GameMode.Adventure)

    assert enums.GameMode.Spectator.is_gamemode(enums.GameMode.Spectator)
    assert enums.GameMode.HardcoreSpectator.is_gamemode(enums.GameMode.Spectator)

    assert enums.GameMode.HardcoreSurvival.is_hardcore
    assert enums.GameMode.HardcoreCreative.is_hardcore
    assert enums.GameMode.HardcoreAdventure.is_hardcore
    assert enums.GameMode.HardcoreSpectator.is_hardcore
