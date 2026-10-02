"""UI strings. Pokemon data itself comes localized from PokeAPI."""

import os

LANGUAGES = ("en", "ko")

MESSAGES = {
    "en": {
        "fetching": "Fetching Pokemon data...",
        "not_found": "Pokemon not found: {query}",
        "gen_not_found": "Generation not found: {gen}",
        "error": "Error: {message}",
        "dex_title": "Pokédex Data",
        "number": "National №",
        "type": "Type",
        "species": "Species",
        "height": "Height",
        "weight": "Weight",
        "abilities": "Abilities",
        "hidden": "hidden ability",
        "generation": "Generation",
        "description": "Description",
        "matchups": "Type Matchups (damage taken)",
        "weak": "Weak",
        "resist": "Resists",
        "immune": "Immune",
        "quiz_title": "Who's that Pokémon?",
        "quiz_prompt": "Your answer ({tries} left, blank to give up)",
        "quiz_hint_type": "Hint: it is {types} type.",
        "quiz_hint_genus": "Hint: it is the {genus}, from generation {gen}.",
        "quiz_hint_letter": "Hint: its name starts with '{letter}'.",
        "quiz_correct": "Correct! It's {name}!",
        "quiz_wrong": "Not quite.",
        "quiz_reveal": "It's {name}!",
        "cache_dir": "Cache directory: {path}",
        "cache_size": "Cached files: {count} ({size:.1f} MB)",
        "cache_cleared": "Cache cleared.",
    },
    "ko": {
        "fetching": "포켓몬 정보를 가져오는 중...",
        "not_found": "포켓몬을 찾을 수 없습니다: {query}",
        "gen_not_found": "세대를 찾을 수 없습니다: {gen}",
        "error": "오류: {message}",
        "dex_title": "포켓몬 도감",
        "number": "전국도감 번호",
        "type": "타입",
        "species": "분류",
        "height": "키",
        "weight": "몸무게",
        "abilities": "특성",
        "hidden": "숨겨진 특성",
        "generation": "세대",
        "description": "설명",
        "matchups": "타입 상성 (받는 데미지)",
        "weak": "약점",
        "resist": "반감",
        "immune": "무효",
        "quiz_title": "이 포켓몬은 누구일까?",
        "quiz_prompt": "정답 입력 ({tries}번 남음, 빈칸이면 포기)",
        "quiz_hint_type": "힌트: {types} 타입입니다.",
        "quiz_hint_genus": "힌트: {gen}세대의 {genus}입니다.",
        "quiz_hint_letter": "힌트: 이름이 '{letter}'(으)로 시작합니다.",
        "quiz_correct": "정답! {name}입니다!",
        "quiz_wrong": "틀렸습니다.",
        "quiz_reveal": "정답은 {name}입니다!",
        "cache_dir": "캐시 폴더: {path}",
        "cache_size": "캐시 파일: {count}개 ({size:.1f} MB)",
        "cache_cleared": "캐시를 비웠습니다.",
    },
}


def default_language() -> str:
    lang = os.environ.get("POKETERM_LANG", "en")
    return lang if lang in LANGUAGES else "en"


def t(lang: str, key: str, **kwargs) -> str:
    template = MESSAGES.get(lang, MESSAGES["en"]).get(key) or MESSAGES["en"][key]
    return template.format(**kwargs)
