import io

import pytest
from PIL import Image
from rich.console import Console

from poketerm.cli import parse_args
from poketerm.pokemon import load_pokemon
from poketerm.quiz import is_correct, run_quiz
from poketerm.render import image_to_text, load_image, silhouette


def test_show_is_the_default_command():
    args = parse_args(["--dex", "--id", "25"])
    assert (args.command, args.id, args.dex) == ("show", "25", True)
    assert parse_args([]).command == "show"
    assert parse_args(["quiz", "--gen", "1"]).gen == 1
    assert parse_args(["cache", "--clear"]).clear


def test_conflicting_options_are_rejected():
    with pytest.raises(SystemExit):
        parse_args(["--id", "25", "--gen", "1"])
    with pytest.raises(SystemExit):
        parse_args(["--id", "25", "--daily"])
    with pytest.raises(SystemExit):
        parse_args(["--size", "0"])


def make_png(size=(40, 20)) -> bytes:
    img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    img.paste((255, 0, 0, 255), (10, 30, 10 + size[0], 30 + size[1]))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def test_load_image_crops_transparent_margin():
    assert load_image(make_png()).size == (40, 20)


def test_image_to_text_dimensions():
    text = image_to_text(load_image(make_png()), width=20)
    lines = text.plain.split("\n")
    assert all(len(line) == 20 for line in lines)
    assert len(lines) == 5  # 20 * (20/40) * 0.96 / 2 rows, rounded


def test_silhouette_keeps_shape_but_hides_colors():
    img = load_image(make_png())
    shadow = silhouette(img)
    assert shadow.getchannel("A").tobytes() == img.getchannel("A").tobytes()
    assert {shadow.getpixel((0, 0))[:3]} == {shadow.getpixel((39, 19))[:3]} != {(255, 0, 0)}


def test_quiz_answers_accept_any_language(api):
    pokemon = load_pokemon(api, 6)
    assert is_correct("charizard", pokemon)
    assert is_correct("리자몽", pokemon)
    assert is_correct("  CHARIZARD ", pokemon)
    assert not is_correct("pikachu", pokemon)
    assert not is_correct("", pokemon)


def run(api, answers, lang="en"):
    pokemon = load_pokemon(api, 6, lang=lang)
    console = Console(file=io.StringIO(), width=60)
    replies = iter(answers)
    won = run_quiz(console, pokemon, load_image(make_png()), 20, lang, ask=lambda _: next(replies))
    return won, console.file.getvalue()


def test_quiz_win_after_hint(api):
    won, output = run(api, ["pikachu", "Charizard"])
    assert won
    assert "Fire/Flying" in output
    assert "Correct! It's Charizard!" in output


def test_quiz_give_up(api):
    won, output = run(api, [""], lang="ko")
    assert not won
    assert "정답은 리자몽입니다!" in output


def test_quiz_out_of_tries(api):
    won, output = run(api, ["a", "b", "c"])
    assert not won
    assert "It's Charizard!" in output
