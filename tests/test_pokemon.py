import datetime as dt

import pytest

from poketerm.api import NotFoundError, resource_key
from poketerm.pokemon import (
    clean_flavor_text,
    daily_species_id,
    load_pokemon,
    parse_pokemon_query,
    species_pool,
)


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("003", (3, 1)),
        ("003-2", (3, 2)),
        ("25", (25, 1)),
        ("mr-mime", ("mr-mime", 1)),
        ("Mr. Mime", ("mr-mime", 1)),
        ("Ho-Oh", ("ho-oh", 1)),
        ("Farfetch'd", ("farfetchd", 1)),
        ("25-abc", ("25-abc", 1)),
    ],
)
def test_parse_pokemon_query(query, expected):
    assert parse_pokemon_query(query) == expected


def test_resource_key_normalizes_paths_and_urls():
    assert resource_key("/api/v2/pokemon/6/") == "pokemon/6"
    assert resource_key("https://pokeapi.co/api/v2/pokemon/6/") == "pokemon/6"
    assert resource_key("pokemon-species?limit=1") == "pokemon-species?limit=1"


def test_clean_flavor_text():
    assert clean_flavor_text("Spits fire that\fis hot\nenough.") == "Spits fire that is hot enough."
    assert clean_flavor_text("Some-­\nthing") == "Some-thing"


def test_load_pokemon_english(api):
    pokemon = load_pokemon(api, 6)
    assert pokemon.display_name == "Charizard"
    assert pokemon.types == ["fire", "flying"]  # sorted by slot
    assert pokemon.genus == "Flame Pokémon"
    assert pokemon.generation == 1
    assert (pokemon.height_m, pokemon.weight_kg) == (1.7, 90.5)
    assert pokemon.flavor_text == "Spits fire that is hot enough."  # latest entry
    assert pokemon.artwork_url == "https://img/6.png"
    assert pokemon.abilities == []  # only fetched with details=True


def test_load_pokemon_korean_with_details(api):
    pokemon = load_pokemon(api, 6, lang="ko", details=True)
    assert pokemon.display_name == "리자몽"
    assert pokemon.genus == "화염포켓몬"
    assert pokemon.flavor_text == "고열의 불꽃을 내뿜는다."
    assert pokemon.abilities == [("맹화", False), ("선파워", True)]
    assert "Charizard" in pokemon.names and "리자몽" in pokemon.names


def test_load_form(api):
    assert load_pokemon(api, 6, form_idx=2).display_name == "Mega Charizard X"
    # Korean full name is missing, and the Korean form name already includes the species.
    assert load_pokemon(api, 6, form_idx=2, lang="ko").display_name == "메가리자몽X"
    # Out-of-range form index falls back to the default form.
    assert load_pokemon(api, 6, form_idx=9).display_name == "Charizard"


def test_load_by_form_name_falls_back_to_pokemon_endpoint(api):
    pokemon = load_pokemon(api, "charizard-mega-x")
    assert pokemon.species_id == 6
    assert pokemon.types == ["fire", "dragon"]


def test_unknown_pokemon_raises_not_found(api):
    with pytest.raises(NotFoundError):
        load_pokemon(api, "missingno")
    with pytest.raises(NotFoundError):
        load_pokemon(api, "../etc")


def test_species_pool(api):
    assert species_pool(api) == list(range(1, 1026))
    assert species_pool(api, gen=1) == [1, 2, 3]
    with pytest.raises(NotFoundError):
        species_pool(api, gen=42)


def test_daily_is_stable_within_a_day(api):
    day = dt.date(2026, 10, 2)
    picks = {daily_species_id(api, day=day) for _ in range(5)}
    assert len(picks) == 1
    week = {daily_species_id(api, day=day + dt.timedelta(days=i)) for i in range(7)}
    assert len(week) > 1


def test_responses_are_cached(api, server):
    load_pokemon(api, 6)
    count = len(server.requests)
    load_pokemon(api, 6)
    assert len(server.requests) == count


def test_corrupt_cache_entry_is_refetched(api, server, tmp_path):
    api.get("pokemon/6")
    (tmp_path / "api" / "pokemon" / "6.json").write_text("{not json")
    assert api.get("pokemon/6")["name"] == "charizard"
    assert len(server.requests) == 2
