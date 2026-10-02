import argparse
import shutil
import sys
from importlib.metadata import version

from rich.console import Console
from rich.text import Text

from poketerm.api import NotFoundError, PokeAPI, PokeTermError
from poketerm.i18n import LANGUAGES, default_language, t
from poketerm.pokemon import (
    daily_species_id,
    load_pokemon,
    parse_pokemon_query,
    random_species_id,
)
from poketerm.quiz import run_quiz
from poketerm.render import art_panel, dex_view, image_to_text, load_image, output_width

COMMANDS = ("show", "quiz", "cache")


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--lang",
        choices=LANGUAGES,
        default=default_language(),
        help="Language for names and Pokédex text (default: $POKETERM_LANG or en)",
    )
    sized = argparse.ArgumentParser(add_help=False)
    sized.add_argument("--size", type=int, help="Image width in characters")

    parser = argparse.ArgumentParser(
        prog="poketerm",
        description="Pokemon artwork and Pokédex info in your terminal. "
        "Runs `show` when no command is given.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {version('poketerm')}")
    commands = parser.add_subparsers(dest="command", required=True)

    show = commands.add_parser("show", parents=[common, sized], help="Show a Pokemon (default)")
    which = show.add_mutually_exclusive_group()
    which.add_argument("--id", help="Pokemon number or name (e.g. 003, 003-2, mr-mime)")
    which.add_argument("--daily", action="store_true", help="Pokemon of the day")
    show.add_argument("--gen", type=int, help="Pick the random/daily Pokemon from this generation")
    show.add_argument("--dex", action="store_true", help="Show Pokédex info and type matchups")

    quiz = commands.add_parser("quiz", parents=[common, sized], help="Who's that Pokémon? quiz")
    quiz.add_argument("--gen", type=int, help="Only ask about Pokemon from this generation")

    cache = commands.add_parser("cache", parents=[common], help="Show or clear the local cache")
    cache.add_argument("--clear", action="store_true", help="Delete all cached data")
    return parser


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = build_parser()
    # Keep `poketerm --dex --id 25` working: default to the `show` command.
    if not argv or (argv[0] not in COMMANDS and argv[0] not in ("-h", "--help", "--version")):
        argv = ["show", *argv]
    args = parser.parse_args(argv)
    if getattr(args, "id", None) and args.gen is not None:
        parser.error("--gen cannot be combined with --id")
    if getattr(args, "size", None) is not None and args.size < 1:
        parser.error("--size must be positive")
    return args


def pick_species(api: PokeAPI, args: argparse.Namespace) -> tuple[int | str, int]:
    try:
        if getattr(args, "daily", False):
            return daily_species_id(api, args.gen), 1
        return random_species_id(api, args.gen), 1
    except NotFoundError:
        raise PokeTermError(t(args.lang, "gen_not_found", gen=args.gen)) from None


def fetch_image(api: PokeAPI, url: str | None, console: Console):
    if not url:
        return None
    try:
        return load_image(api.get_bytes(url))
    except PokeTermError as e:
        console.print(Text(f"Could not load image: {e}", style="dim"))
        return None


def cmd_show(api: PokeAPI, args: argparse.Namespace, console: Console) -> None:
    lang = args.lang
    with console.status(f"[bold green]{t(lang, 'fetching')}"):
        query, form_idx = parse_pokemon_query(args.id) if args.id else pick_species(api, args)
        try:
            pokemon = load_pokemon(api, query, form_idx, lang, details=args.dex)
        except NotFoundError:
            raise PokeTermError(t(lang, "not_found", query=args.id or query)) from None
        image = fetch_image(api, pokemon.artwork_url, console)

    width = output_width(console.width, args.size)
    art = image_to_text(image, width) if image else Text("?")
    console.print(art_panel(pokemon, art, lang))
    if args.dex:
        console.print(
            dex_view(pokemon, lang, args.size + 4 if args.size else min(console.width, 100))
        )


def cmd_quiz(api: PokeAPI, args: argparse.Namespace, console: Console) -> None:
    with console.status(f"[bold green]{t(args.lang, 'fetching')}"):
        for _ in range(5):  # A few species lack artwork; just pick another.
            species_id, _form = pick_species(api, args)
            pokemon = load_pokemon(api, species_id, lang=args.lang)
            image = fetch_image(api, pokemon.artwork_url, console)
            if image:
                break
        else:
            raise PokeTermError("Could not find a Pokemon with artwork")
    run_quiz(console, pokemon, image, output_width(console.width, args.size), args.lang)


def cmd_cache(api: PokeAPI, args: argparse.Namespace, console: Console) -> None:
    path = api.cache_dir
    if args.clear:
        shutil.rmtree(path, ignore_errors=True)
        console.print(t(args.lang, "cache_cleared"))
        return
    files = [f for f in path.rglob("*") if f.is_file()] if path.exists() else []
    size_mb = sum(f.stat().st_size for f in files) / 1_000_000
    console.print(Text(t(args.lang, "cache_dir", path=path)))
    console.print(t(args.lang, "cache_size", count=len(files), size=size_mb))


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    console = Console()
    api = PokeAPI()
    handler = {"show": cmd_show, "quiz": cmd_quiz, "cache": cmd_cache}[args.command]
    try:
        handler(api, args, console)
    except PokeTermError as e:
        console.print(Text(t(args.lang, "error", message=e), style="bold red"))
        return 1
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
