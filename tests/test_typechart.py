from poketerm.typechart import DAMAGE_CHART, TYPE_COLORS, TYPE_NAMES_KO, defensive_multipliers


def test_chart_covers_all_types():
    assert set(DAMAGE_CHART) == set(TYPE_COLORS) == set(TYPE_NAMES_KO)
    for row in DAMAGE_CHART.values():
        assert set(row) <= set(DAMAGE_CHART)


def test_dual_type_multipliers_combine():
    charizard = defensive_multipliers(["fire", "flying"])
    assert charizard["rock"] == 4
    assert charizard["water"] == 2
    assert charizard["grass"] == 0.25
    assert charizard["ground"] == 0
    assert charizard["normal"] == 1


def test_immunities():
    assert defensive_multipliers(["ghost"])["normal"] == 0
    assert defensive_multipliers(["fairy"])["dragon"] == 0
    assert defensive_multipliers(["steel"])["poison"] == 0


def test_unknown_types_are_neutral():
    assert defensive_multipliers(["stellar"]) == defensive_multipliers([])
