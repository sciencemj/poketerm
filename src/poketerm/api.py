"""Small PokeAPI client with an on-disk cache.

PokeAPI data almost never changes, so responses are cached indefinitely;
`poketerm cache --clear` wipes them.
"""

import hashlib
import json
import os
import re
from pathlib import Path

import httpx
from platformdirs import user_cache_dir

API_BASE = "https://pokeapi.co/api/v2/"


class PokeTermError(Exception):
    """An error with a message that is safe to show to the user."""


class NotFoundError(PokeTermError):
    pass


def default_cache_dir() -> Path:
    return Path(os.environ.get("POKETERM_CACHE_DIR") or user_cache_dir("poketerm"))


def resource_key(resource: str) -> str:
    """Normalize "pokemon/6", "/api/v2/pokemon/6/" or a full URL to "pokemon/6"."""
    path = resource.split("/api/v2/", 1)[-1]
    path, _, query = path.partition("?")
    path = path.strip("/")
    return f"{path}?{query}" if query else path


def id_from_url(url: str) -> int:
    return int(url.rstrip("/").rsplit("/", 1)[-1])


class PokeAPI:
    def __init__(self, cache_dir: Path | None = None, client: httpx.Client | None = None):
        self.cache_dir = cache_dir if cache_dir is not None else default_cache_dir()
        self.client = client or httpx.Client(timeout=15, follow_redirects=True)

    def _cache_path(self, *parts: str) -> Path:
        return self.cache_dir.joinpath(*parts)

    def _read_cache(self, path: Path) -> bytes | None:
        try:
            return path.read_bytes()
        except OSError:
            return None

    def _write_cache(self, path: Path, data: bytes) -> None:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(path.suffix + ".tmp")
            tmp.write_bytes(data)
            tmp.replace(path)
        except OSError:
            pass  # A read-only cache dir should not break the CLI.

    def _fetch(self, url: str) -> bytes:
        try:
            response = self.client.get(url)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise NotFoundError(url) from e
            raise PokeTermError(f"HTTP {e.response.status_code}: {url}") from e
        except httpx.HTTPError as e:
            raise PokeTermError(f"Network error ({e.__class__.__name__}): {url}") from e
        return response.content

    def get(self, resource: str) -> dict:
        key = resource_key(resource)
        path = self._cache_path("api", re.sub(r"[^\w/-]", "_", key) + ".json")
        cached = self._read_cache(path)
        if cached is not None:
            try:
                return json.loads(cached)
            except ValueError:
                pass  # Corrupt cache entry: fetch it again.

        endpoint, _, query = key.partition("?")
        url = API_BASE + endpoint + "/" + (f"?{query}" if query else "")
        data = self._fetch(url)
        result = json.loads(data)
        self._write_cache(path, data)
        return result

    def get_bytes(self, url: str) -> bytes:
        name = hashlib.sha256(url.encode()).hexdigest()[:24] + Path(url).suffix
        path = self._cache_path("files", name)
        cached = self._read_cache(path)
        if cached is not None:
            return cached
        data = self._fetch(url)
        self._write_cache(path, data)
        return data
