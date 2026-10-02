"""'Who's that Pokémon?' — guess the Pokemon from its silhouette."""

import re
from collections.abc import Callable

from rich.console import Console
from rich.text import Text

from poketerm.i18n import t
from poketerm.pokemon import Pokemon
from poketerm.render import art_panel, image_to_text, silhouette
from poketerm.typechart import type_name

MAX_TRIES = 3


def normalize_answer(answer: str) -> str:
    """Case- and punctuation-insensitive form: "Mr. Mime" == "mr-mime" == "MrMime"."""
    return re.sub(r"[\W_]+", "", answer.casefold())


def is_correct(answer: str, pokemon: Pokemon) -> bool:
    guess = normalize_answer(answer)
    return bool(guess) and any(guess == normalize_answer(name) for name in pokemon.names)


def hint(pokemon: Pokemon, attempt: int, lang: str) -> str:
    if attempt == 1:
        types = "/".join(type_name(type_, lang) for type_ in pokemon.types)
        return t(lang, "quiz_hint_type", types=types)
    if attempt == 2 and pokemon.genus:
        return t(lang, "quiz_hint_genus", genus=pokemon.genus, gen=pokemon.generation)
    return t(lang, "quiz_hint_letter", letter=pokemon.display_name[0])


def run_quiz(
    console: Console,
    pokemon: Pokemon,
    image,
    width: int,
    lang: str,
    ask: Callable[[str], str] | None = None,
) -> bool:
    """Play one round. Returns True when the player guessed right."""
    ask = ask or console.input
    console.print(art_panel(pokemon, image_to_text(silhouette(image), width), lang, reveal=False))

    correct = False
    for attempt in range(1, MAX_TRIES + 1):
        try:
            answer = ask(f"[bold]{t(lang, 'quiz_prompt', tries=MAX_TRIES - attempt + 1)}[/bold]: ")
        except EOFError:
            answer = ""
        if not answer.strip():
            break
        if is_correct(answer, pokemon):
            correct = True
            break
        console.print(f"[red]{t(lang, 'quiz_wrong')}[/red]", end=" ")
        if attempt < MAX_TRIES:
            console.print(hint(pokemon, attempt, lang))
        else:
            console.print()

    console.print(art_panel(pokemon, image_to_text(image, width), lang))
    key = "quiz_correct" if correct else "quiz_reveal"
    color = "green" if correct else "yellow"
    console.print(Text(t(lang, key, name=pokemon.display_name), style=f"bold {color}"))
    return correct
