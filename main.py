import argparse
import io
import random
import sys

import httpx
from bs4 import BeautifulSoup
from PIL import Image
from rich.console import Console
from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.text import Text


def get_pokemon_id_and_name(input_id=None):
    if input_id is None:
        species_id = random.randint(1, 1025)
        form_idx = 1
    else:
        parts = str(input_id).split("-")
        try:
            species_id = int(parts[0])
        except ValueError:
            species_id = parts[0].lower()

        form_idx = int(parts[1]) if len(parts) > 1 else 1

    try:
        response = httpx.get(f"https://pokeapi.co/api/v2/pokemon-species/{species_id}/")
        response.raise_for_status()
        data = response.json()

        varieties = data["varieties"]
        if form_idx > len(varieties):
            form_idx = 1

        target_pokemon = varieties[form_idx - 1]["pokemon"]
        pokemon_name = target_pokemon["name"]
        pokemon_id = target_pokemon["url"].split("/")[-2]

        display_name = data["name"].capitalize()
        if len(varieties) > 1 and form_idx > 1:
            suffix = (
                pokemon_name.replace(data["name"], "")
                .strip("-")
                .replace("-", " ")
                .capitalize()
            )
            if suffix:
                display_name += f" ({suffix})"
            else:
                display_name += f" (Form {form_idx})"

        return pokemon_id, pokemon_name, display_name, data["name"]
    except Exception as e:
        print(f"Error fetching pokemon data: {e}")
        sys.exit(1)


def get_ascii_image(image_url, width=None, size=None):
    try:
        response = httpx.get(image_url)
        response.raise_for_status()
        img = Image.open(io.BytesIO(response.content)).convert("RGBA")
    except Exception as e:
        return Text(f"Error loading image: {e}")

    console = Console()
    original_width, original_height = img.size
    aspect_ratio = original_height / original_width

    if size:
        width = size
    else:
        if width is None:
            width = console.width
        width = min(width - 4, 100)

    height_chars = int(width * aspect_ratio * 0.48)
    img = img.resize((width, height_chars * 2), Image.Resampling.LANCZOS)

    text = Text()
    for y in range(0, img.height, 2):
        for x in range(img.width):
            r1, g1, b1, a1 = img.getpixel((x, y))
            if y + 1 < img.height:
                r2, g2, b2, a2 = img.getpixel((x, y + 1))
            else:
                r2, g2, b2, a2 = (0, 0, 0, 0)

            fg_color = f"rgb({r2},{g2},{b2})" if a2 > 128 else None
            bg_color = f"rgb({r1},{g1},{b1})" if a1 > 128 else None

            if fg_color and bg_color:
                text.append("▄", style=Style(color=fg_color, bgcolor=bg_color))
            elif fg_color:
                text.append("▄", style=Style(color=fg_color))
            elif bg_color:
                text.append("▀", style=Style(color=bg_color))
            else:
                text.append(" ")
        if y + 2 < img.height:
            text.append("\n")
    return text


def scrape_dex_info(base_name):
    url = f"https://pokemondb.net/pokedex/{base_name}"
    try:
        # Use a real browser-like User-Agent
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = httpx.get(url, headers=headers, follow_redirects=True)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")

        info = {}
        vitals = soup.find("div", class_="grid-col span-md-6 span-lg-4")
        if vitals:
            table = vitals.find("table", class_="vitals-table")
            if table:
                for row in table.find_all("tr"):
                    th = row.find("th")
                    td = row.find("td")
                    if th and td:
                        key = th.text.strip()
                        if key.lower() == "abilities":
                            parts = list(td.stripped_strings)
                            formatted = []
                            current_prefix = ""
                            for p in parts:
                                if p.endswith(".") and len(p) <= 3:
                                    current_prefix = p + " "
                                elif p.startswith("("):
                                    if formatted:
                                        formatted[-1] += " " + p
                                    else:
                                        formatted.append(p)
                                else:
                                    formatted.append(current_prefix + p)
                                    current_prefix = ""
                            info[key] = "\n".join(formatted)
                        else:
                            info[key] = td.text.strip()

        flavor_text = ""
        # Look for ANY cell-med-text first
        cell = soup.find("td", class_="cell-med-text")
        if cell:
            flavor_text = cell.text.strip()

        return info, flavor_text
    except Exception as e:
        return None, f"Could not scrape dex info: {e}"


def main():
    parser = argparse.ArgumentParser(description="Random Pokemon ASCII Art Generator")
    parser.add_argument("--dex", action="store_true", help="Show Pokedex info")
    parser.add_argument("--id", type=str, help="Specific Pokemon ID (e.g., 003, 003-2)")
    parser.add_argument(
        "--size", type=int, help="Output size in characters (e.g., 10 for 10x10)"
    )
    args = parser.parse_args()

    console = Console()

    with console.status("[bold green]Fetching Pokemon data..."):
        p_id, p_name_api, display_name, base_name = get_pokemon_id_and_name(args.id)

    image_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{p_id}.png"

    ascii_art = get_ascii_image(image_url, size=args.size)

    console.print(
        Panel(
            ascii_art,
            title=f"[bold]{display_name} (#{p_id})[/bold]",
            expand=False,
            border_style="bold magenta",
        )
    )

    if args.dex:
        with console.status("[bold blue]Scraping Pokedex info..."):
            info, flavor = scrape_dex_info(base_name)

        target_width = args.size if args.size else min(console.width, 100)

        if info:
            table = Table(
                title="Pokédex Data",
                show_header=True,
                header_style="bold cyan",
                width=target_width,
            )
            table.add_column("Category", style="dim")
            table.add_column("Value")
            for k, v in info.items():
                if k.lower() != "local №":
                    table.add_row(k, v)
            console.print(table)

        if flavor:
            console.print(
                Panel(
                    flavor,
                    title="Description",
                    border_style="green",
                    width=target_width,
                )
            )


if __name__ == "__main__":
    main()
