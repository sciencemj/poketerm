"""Rich renderables for Pokemon artwork and Pokédex data."""

import io

from PIL import Image
from rich.console import Group
from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.text import Text

from poketerm.i18n import t
from poketerm.pokemon import Pokemon
from poketerm.typechart import TYPE_COLORS, defensive_multipliers, type_name

MAX_WIDTH = 100
SILHOUETTE_COLOR = (110, 110, 130)


def load_image(data: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(data)).convert("RGBA")
    # Official artwork has wide transparent margins; crop them to keep detail.
    bbox = img.getchannel("A").getbbox()
    return img.crop(bbox) if bbox else img


def silhouette(img: Image.Image) -> Image.Image:
    shadow = Image.new("RGBA", img.size, SILHOUETTE_COLOR + (255,))
    shadow.putalpha(img.getchannel("A"))
    return shadow


def output_width(console_width: int, size: int | None = None) -> int:
    """Width of the image in characters (the panel adds 4 for borders and padding)."""
    if size:
        return size
    return max(min(console_width - 4, MAX_WIDTH), 10)


def image_to_text(img: Image.Image, width: int) -> Text:
    """Draw an image with half blocks: each character cell holds two pixels."""
    aspect_ratio = img.height / img.width
    # Terminal cells are about twice as tall as wide, so one cell = 1x2 pixels.
    height = max(round(width * aspect_ratio * 0.96 / 2) * 2, 2)
    img = img.resize((width, height), Image.Resampling.LANCZOS)
    pixels = img.load()

    text = Text()
    for y in range(0, height, 2):
        if y:
            text.append("\n")
        for x in range(width):
            r1, g1, b1, a1 = pixels[x, y]
            r2, g2, b2, a2 = pixels[x, y + 1]
            top = f"rgb({r1},{g1},{b1})" if a1 > 128 else None
            bottom = f"rgb({r2},{g2},{b2})" if a2 > 128 else None

            if top and bottom:
                text.append("▄", style=Style(color=bottom, bgcolor=top))
            elif bottom:
                text.append("▄", style=Style(color=bottom))
            elif top:
                text.append("▀", style=Style(color=top))
            else:
                text.append(" ")
    return text


def _text_color_on(hex_color: str) -> str:
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    return "black" if luminance > 150 else "white"


def type_badge(type_: str, lang: str) -> Text:
    color = TYPE_COLORS.get(type_, "#888888")
    return Text(f" {type_name(type_, lang)} ", style=f"bold {_text_color_on(color)} on {color}")


def type_badges(types: list[str], lang: str) -> Text:
    return Text(" ").join(type_badge(type_, lang) for type_ in types)


def border_color(pokemon: Pokemon) -> str:
    return TYPE_COLORS.get(pokemon.types[0], "magenta") if pokemon.types else "magenta"


def art_panel(pokemon: Pokemon, art: Text, lang: str, reveal: bool = True) -> Panel:
    """Artwork framed in the Pokemon's type color; hidden details for the quiz."""
    if not reveal:
        return Panel(art, title=f"[bold]{t(lang, 'quiz_title')}[/bold]", expand=False)
    title = Text.assemble((pokemon.display_name, "bold"), f" (#{pokemon.species_id:04d})")
    return Panel(
        art,
        title=title,
        subtitle=type_badges(pokemon.types, lang),
        expand=False,
        border_style=border_color(pokemon),
    )


def dex_table(pokemon: Pokemon, lang: str, width: int) -> Table:
    table = Table(title=t(lang, "dex_title"), show_header=False, width=width)
    table.add_column(style="bold cyan", no_wrap=True)
    table.add_column()
    table.add_row(t(lang, "number"), f"{pokemon.species_id:04d}")
    table.add_row(t(lang, "type"), type_badges(pokemon.types, lang))
    table.add_row(t(lang, "species"), pokemon.genus)
    table.add_row(t(lang, "height"), f"{pokemon.height_m:g} m")
    table.add_row(t(lang, "weight"), f"{pokemon.weight_kg:g} kg")
    if pokemon.abilities:
        lines = [
            f"{name} ({t(lang, 'hidden')})" if hidden else name
            for name, hidden in pokemon.abilities
        ]
        table.add_row(t(lang, "abilities"), "\n".join(lines))
    table.add_row(t(lang, "generation"), str(pokemon.generation))
    return table


def matchup_panel(pokemon: Pokemon, lang: str, width: int) -> Panel:
    multipliers = defensive_multipliers(pokemon.types)
    groups = [
        (t(lang, "weak"), "×4", 4),
        (t(lang, "weak"), "×2", 2),
        (t(lang, "resist"), "×½", 0.5),
        (t(lang, "resist"), "×¼", 0.25),
        (t(lang, "immune"), "×0", 0),
    ]
    table = Table.grid(padding=(0, 1))
    table.add_column(style="bold", no_wrap=True)
    table.add_column()
    for label, mark, value in groups:
        attackers = [a for a, m in multipliers.items() if m == value]
        if attackers:
            table.add_row(f"{label} {mark}", type_badges(attackers, lang))
    return Panel(table, title=t(lang, "matchups"), border_style="yellow", width=width)


def dex_view(pokemon: Pokemon, lang: str, width: int) -> Group:
    parts = [dex_table(pokemon, lang, width), matchup_panel(pokemon, lang, width)]
    if pokemon.flavor_text:
        parts.append(
            Panel(
                pokemon.flavor_text, title=t(lang, "description"), border_style="green", width=width
            )
        )
    return Group(*parts)
