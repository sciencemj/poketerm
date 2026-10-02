"""Pokemon type metadata: colors, Korean names and the damage chart (Gen 6+)."""

TYPE_COLORS = {
    "normal": "#A8A77A",
    "fire": "#EE8130",
    "water": "#6390F0",
    "electric": "#F7D02C",
    "grass": "#7AC74C",
    "ice": "#96D9D6",
    "fighting": "#C22E28",
    "poison": "#A33EA1",
    "ground": "#E2BF65",
    "flying": "#A98FF3",
    "psychic": "#F95587",
    "bug": "#A6B91A",
    "rock": "#B6A136",
    "ghost": "#735797",
    "dragon": "#6F35FC",
    "dark": "#705746",
    "steel": "#B7B7CE",
    "fairy": "#D685AD",
}

TYPE_NAMES_KO = {
    "normal": "노말",
    "fire": "불꽃",
    "water": "물",
    "electric": "전기",
    "grass": "풀",
    "ice": "얼음",
    "fighting": "격투",
    "poison": "독",
    "ground": "땅",
    "flying": "비행",
    "psychic": "에스퍼",
    "bug": "벌레",
    "rock": "바위",
    "ghost": "고스트",
    "dragon": "드래곤",
    "dark": "악",
    "steel": "강철",
    "fairy": "페어리",
}

# Attacking type -> {defending type: multiplier}; pairs not listed are 1x.
DAMAGE_CHART = {
    "normal": {"rock": 0.5, "ghost": 0, "steel": 0.5},
    "fire": {
        "fire": 0.5, "water": 0.5, "grass": 2, "ice": 2,
        "bug": 2, "rock": 0.5, "dragon": 0.5, "steel": 2,
    },
    "water": {
        "fire": 2, "water": 0.5, "grass": 0.5, "ground": 2, "rock": 2, "dragon": 0.5,
    },
    "electric": {
        "water": 2, "electric": 0.5, "grass": 0.5,
        "ground": 0, "flying": 2, "dragon": 0.5,
    },
    "grass": {
        "fire": 0.5, "water": 2, "grass": 0.5, "poison": 0.5, "ground": 2,
        "flying": 0.5, "bug": 0.5, "rock": 2, "dragon": 0.5, "steel": 0.5,
    },
    "ice": {
        "fire": 0.5, "water": 0.5, "grass": 2, "ice": 0.5,
        "ground": 2, "flying": 2, "dragon": 2, "steel": 0.5,
    },
    "fighting": {
        "normal": 2, "ice": 2, "poison": 0.5, "flying": 0.5, "psychic": 0.5,
        "bug": 0.5, "rock": 2, "ghost": 0, "dark": 2, "steel": 2, "fairy": 0.5,
    },
    "poison": {
        "grass": 2, "poison": 0.5, "ground": 0.5, "rock": 0.5,
        "ghost": 0.5, "steel": 0, "fairy": 2,
    },
    "ground": {
        "fire": 2, "electric": 2, "grass": 0.5, "poison": 2,
        "flying": 0, "bug": 0.5, "rock": 2, "steel": 2,
    },
    "flying": {
        "electric": 0.5, "grass": 2, "fighting": 2, "bug": 2, "rock": 0.5, "steel": 0.5,
    },
    "psychic": {"fighting": 2, "poison": 2, "psychic": 0.5, "dark": 0, "steel": 0.5},
    "bug": {
        "fire": 0.5, "grass": 2, "fighting": 0.5, "poison": 0.5, "flying": 0.5,
        "psychic": 2, "ghost": 0.5, "dark": 2, "steel": 0.5, "fairy": 0.5,
    },
    "rock": {
        "fire": 2, "ice": 2, "fighting": 0.5, "ground": 0.5,
        "flying": 2, "bug": 2, "steel": 0.5,
    },
    "ghost": {"normal": 0, "psychic": 2, "ghost": 2, "dark": 0.5},
    "dragon": {"dragon": 2, "steel": 0.5, "fairy": 0},
    "dark": {"fighting": 0.5, "psychic": 2, "ghost": 2, "dark": 0.5, "fairy": 0.5},
    "steel": {
        "fire": 0.5, "water": 0.5, "electric": 0.5, "ice": 2,
        "rock": 2, "steel": 0.5, "fairy": 2,
    },
    "fairy": {
        "fire": 0.5, "fighting": 2, "poison": 0.5, "dragon": 2, "dark": 2, "steel": 0.5,
    },
}  # fmt: skip


def type_name(type_: str, lang: str) -> str:
    if lang == "ko":
        return TYPE_NAMES_KO.get(type_, type_)
    return type_.capitalize()


def defensive_multipliers(defending: list[str]) -> dict[str, float]:
    """Damage multiplier each attacking type deals to a Pokemon of these types.

    Types outside the 18 standard ones (e.g. "stellar") are treated as neutral.
    """
    result = {}
    for attacker, chart in DAMAGE_CHART.items():
        multiplier = 1.0
        for defender in defending:
            multiplier *= chart.get(defender, 1)
        result[attacker] = multiplier
    return result
