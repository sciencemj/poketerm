"""Turning user input into Pokemon data fetched from PokeAPI."""

import datetime as dt
import random
import re
from dataclasses import dataclass, field

from poketerm.api import NotFoundError, PokeAPI, id_from_url


@dataclass
class Pokemon:
    pokemon_id: int  # PokeAPI pokemon id; alternate forms use ids above 10000
    species_id: int  # National Pokédex number
    name: str  # PokeAPI name, e.g. "charizard-mega-x"
    display_name: str
    names: list[str]  # Species name in every language, for quiz answers
    types: list[str]
    genus: str
    generation: int
    height_m: float
    weight_kg: float
    flavor_text: str
    artwork_url: str | None
    abilities: list[tuple[str, bool]] = field(default_factory=list)  # (name, hidden)


def parse_pokemon_query(input_id):
    """Split user input into (species, form index).

    Numeric input may carry a form suffix ("003", "003-2"); anything else is
    a species name, which can itself contain hyphens ("mr-mime", "ho-oh").
    """
    query = str(input_id).strip().lower()
    match = re.fullmatch(r"(\d+)(?:-(\d+))?", query)
    if match:
        return int(match.group(1)), int(match.group(2) or 1)
    # PokeAPI names drop punctuation: "Mr. Mime" -> "mr-mime", "Farfetch'd" -> "farfetchd"
    name = re.sub(r"[.'’]", "", query)
    name = re.sub(r"\s+", "-", name)
    return name, 1


def localized(entries: list[dict], lang: str, key: str = "name") -> str | None:
    """Pick the entry for `lang` (falling back to English) from a PokeAPI names list."""
    by_lang = {}
    for entry in entries:
        by_lang[entry["language"]["name"]] = entry[key]  # later entries win
    return by_lang.get(lang) or by_lang.get("en")


def clean_flavor_text(text: str) -> str:
    text = text.replace("­\n", "").replace("­", "")
    return re.sub(r"\s+", " ", text).strip()


def species_pool(api: PokeAPI, gen: int | None = None) -> list[int]:
    """National Pokédex numbers to pick random Pokemon from."""
    if gen is None:
        count = api.get("pokemon-species?limit=1")["count"]
        return list(range(1, count + 1))
    generation = api.get(f"generation/{gen}")
    return sorted(id_from_url(s["url"]) for s in generation["pokemon_species"])


def random_species_id(api: PokeAPI, gen: int | None = None) -> int:
    return random.choice(species_pool(api, gen))


def daily_species_id(api: PokeAPI, gen: int | None = None, day: dt.date | None = None) -> int:
    """The same Pokemon all day long, different every day."""
    day = day or dt.date.today()
    return random.Random(day.toordinal()).choice(species_pool(api, gen))


def _display_name(api: PokeAPI, species: dict, pokemon: dict, lang: str) -> str:
    species_name = localized(species["names"], lang) or species["name"].capitalize()
    if pokemon["is_default"] or not pokemon["forms"]:
        return species_name

    form = api.get(pokemon["forms"][0]["url"])
    full_names = {n["language"]["name"]: n["name"] for n in form["names"]}
    if lang in full_names:
        return full_names[lang]  # e.g. "Mega Charizard X"
    form_name = localized(form["form_names"], lang)
    if not form_name:
        suffix = pokemon["name"].removeprefix(species["name"]).strip("-")
        form_name = suffix.replace("-", " ").capitalize()
    if not form_name:
        return species_name
    # An English fallback may repeat the English species name ("Pikachu Rock Star").
    english_name = localized(species["names"], "en") or ""
    if english_name and english_name != form_name:
        form_name = form_name.replace(english_name, "").strip()
    if species_name in form_name:  # Some form names are already full names ("메가리자몽X")
        return form_name
    return f"{species_name} ({form_name})"


def load_pokemon(
    api: PokeAPI,
    species_query: int | str,
    form_idx: int = 1,
    lang: str = "en",
    details: bool = False,
) -> Pokemon:
    """Fetch a Pokemon by National Pokédex number or name.

    `form_idx` selects among the species' varieties (1 = default form); an
    out-of-range index falls back to the default form. With `details`, the
    ability names are fetched too (one extra request per ability).
    """
    if isinstance(species_query, str) and not re.fullmatch(r"[a-z0-9-]+", species_query):
        raise NotFoundError(species_query)
    try:
        species = api.get(f"pokemon-species/{species_query}")
    except NotFoundError:
        # Form names like "charizard-mega-x" are pokemon, not species.
        pokemon = api.get(f"pokemon/{species_query}")
        species = api.get(pokemon["species"]["url"])
    else:
        varieties = species["varieties"]
        if not 1 <= form_idx <= len(varieties):
            form_idx = 1
        pokemon = api.get(varieties[form_idx - 1]["pokemon"]["url"])

    artwork = pokemon["sprites"].get("other", {}).get("official-artwork", {})
    flavor_entries = [
        e for e in species["flavor_text_entries"] if e["language"]["name"] in (lang, "en")
    ]
    flavor = localized(flavor_entries, lang, "flavor_text") or ""

    result = Pokemon(
        pokemon_id=pokemon["id"],
        species_id=species["id"],
        name=pokemon["name"],
        display_name=_display_name(api, species, pokemon, lang),
        names=[n["name"] for n in species["names"]] + [species["name"]],
        types=[t["type"]["name"] for t in sorted(pokemon["types"], key=lambda t: t["slot"])],
        genus=localized(species["genera"], lang, "genus") or "",
        generation=id_from_url(species["generation"]["url"]),
        height_m=pokemon["height"] / 10,
        weight_kg=pokemon["weight"] / 10,
        flavor_text=clean_flavor_text(flavor),
        artwork_url=artwork.get("front_default") or pokemon["sprites"].get("front_default"),
    )
    if details:
        for entry in sorted(pokemon["abilities"], key=lambda a: a["slot"]):
            ability = api.get(entry["ability"]["url"])
            name = localized(ability["names"], lang) or ability["name"]
            result.abilities.append((name, entry["is_hidden"]))
    return result
