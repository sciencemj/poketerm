import json

import httpx
import pytest

from poketerm.api import PokeAPI


def names(**by_lang):
    return [{"name": name, "language": {"name": lang}} for lang, name in by_lang.items()]


# Minimal PokeAPI responses, keyed by path under /api/v2/.
RESOURCES = {
    "pokemon-species/6": {
        "id": 6,
        "name": "charizard",
        "names": names(ko="리자몽", en="Charizard"),
        "genera": [
            {"genus": "Flame Pokémon", "language": {"name": "en"}},
            {"genus": "화염포켓몬", "language": {"name": "ko"}},
        ],
        "generation": {"url": "/api/v2/generation/1/"},
        "flavor_text_entries": [
            {"flavor_text": "Old\ntext.", "language": {"name": "en"}},
            {"flavor_text": "Spits fire that\fis hot\nenough.", "language": {"name": "en"}},
            {"flavor_text": "고열의\n불꽃을 내뿜는다.", "language": {"name": "ko"}},
        ],
        "varieties": [
            {"is_default": True, "pokemon": {"name": "charizard", "url": "/api/v2/pokemon/6/"}},
            {
                "is_default": False,
                "pokemon": {"name": "charizard-mega-x", "url": "/api/v2/pokemon/10034/"},
            },
        ],
    },
    "pokemon/6": {
        "id": 6,
        "name": "charizard",
        "is_default": True,
        "height": 17,
        "weight": 905,
        "species": {"url": "/api/v2/pokemon-species/6/"},
        "forms": [{"url": "/api/v2/pokemon-form/6/"}],
        "types": [
            {"slot": 2, "type": {"name": "flying"}},
            {"slot": 1, "type": {"name": "fire"}},
        ],
        "abilities": [
            {"slot": 3, "is_hidden": True, "ability": {"url": "/api/v2/ability/94/"}},
            {"slot": 1, "is_hidden": False, "ability": {"url": "/api/v2/ability/66/"}},
        ],
        "sprites": {"other": {"official-artwork": {"front_default": "https://img/6.png"}}},
    },
    "pokemon/10034": {
        "id": 10034,
        "name": "charizard-mega-x",
        "is_default": False,
        "height": 17,
        "weight": 1105,
        "species": {"url": "/api/v2/pokemon-species/6/"},
        "forms": [{"url": "/api/v2/pokemon-form/10134/"}],
        "types": [{"slot": 1, "type": {"name": "fire"}}, {"slot": 2, "type": {"name": "dragon"}}],
        "abilities": [],
        "sprites": {"other": {"official-artwork": {"front_default": None}}},
    },
    "pokemon/charizard-mega-x": "pokemon/10034",
    "pokemon-form/10134": {
        "names": names(en="Mega Charizard X"),
        "form_names": names(ko="메가리자몽X", en="Mega Charizard X"),
    },
    "ability/66": {"name": "blaze", "names": names(ko="맹화", en="Blaze")},
    "ability/94": {"name": "solar-power", "names": names(ko="선파워", en="Solar Power")},
    "pokemon-species": {"count": 1025},
    "generation/1": {
        "pokemon_species": [
            {"url": "/api/v2/pokemon-species/3/"},
            {"url": "/api/v2/pokemon-species/1/"},
            {"url": "/api/v2/pokemon-species/2/"},
        ]
    },
}


class FakeServer:
    def __init__(self):
        self.requests = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(str(request.url))
        key = request.url.path.removeprefix("/api/v2/").strip("/")
        data = RESOURCES.get(key)
        if isinstance(data, str):
            data = RESOURCES[data]
        if data is None:
            return httpx.Response(404)
        return httpx.Response(200, content=json.dumps(data).encode())


@pytest.fixture
def server():
    return FakeServer()


@pytest.fixture
def api(tmp_path, server):
    return PokeAPI(cache_dir=tmp_path, client=httpx.Client(transport=httpx.MockTransport(server)))
