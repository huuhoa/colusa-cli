import hashlib
import pathlib
import shutil
import sys
from typing import Optional

import ssl

import chardet
import requests


class Downloader:
    UserAgent: str = (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/605.1.15 (KHTML, like Gecko) '
        'Version/15.1 Safari/605.1.15'
    )
    DefaultCacheDir: pathlib.Path = pathlib.Path.home() / '.cache' / 'colusa-cli'

    def __init__(self, cache_dir: Optional[pathlib.Path] = None, ssl_cert: Optional[str] = None) -> None:
        self.cache_dir = cache_dir or self.DefaultCacheDir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ssl_cert = ssl_cert

    def _cache_path(self, url: str) -> pathlib.Path:
        digest = hashlib.sha256(url.encode()).hexdigest()
        return self.cache_dir / digest

    def fetch(self, url: str, no_cache: bool = False) -> str:
        """Return page HTML as a string, using disk cache by default."""
        if url.startswith('file://'):
            local_path = pathlib.Path(url.removeprefix('file://'))
            raw = local_path.read_bytes()
            return self._decode(raw)

        cached = self._cache_path(url)
        if cached.exists() and not no_cache:
            raw = cached.read_bytes()
            return self._decode(raw)

        headers = {
            'Accept': '*/*',
            'User-Agent': self.UserAgent,
        }
        verify: str | bool = self.ssl_cert or ssl.get_default_verify_paths().cafile or True
        resp = requests.get(url, headers=headers, timeout=30, verify=verify)
        resp.raise_for_status()
        raw = resp.content
        cached.write_bytes(raw)
        return self._decode(raw)

    @staticmethod
    def _decode(raw: bytes) -> str:
        detected = chardet.detect(raw)
        encoding = detected.get('encoding') or 'utf-8'
        return raw.decode(encoding, errors='replace')
