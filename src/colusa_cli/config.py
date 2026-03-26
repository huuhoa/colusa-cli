import fnmatch
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from .etr import SiteRule


@dataclass
class Config:
    ssl_cert: str | None = None
    cache_dir: Path | None = None
    doh: str | None = None
    browser: bool = False
    sites: list[tuple[str, SiteRule]] = field(default_factory=list)


class ConfigError(Exception):
    pass


def _load_file(path: Path) -> dict:
    """Parse a TOML config file. Returns empty dict if missing, raises ConfigError if malformed."""
    if not path.exists():
        return {}
    try:
        with path.open('rb') as f:
            return tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f'Invalid TOML in {path}: {exc}') from exc


def _parse_site_rules(raw: dict) -> list[tuple[str, SiteRule]]:
    """Extract [sites.*] tables into (pattern, SiteRule) tuples."""
    sites_raw = raw.get('sites', {})
    rules = []
    for pattern, table in sites_raw.items():
        rule = SiteRule(
            content=table.get('content', ''),
            title=table.get('title', ''),
            author=table.get('author', ''),
            published=table.get('published', ''),
            cleanup=table.get('cleanup', []),
            browser=table.get('browser', False),
        )
        rules.append((pattern, rule))
    return rules


def load_config(
    project_path: Path = Path('.colusa'),
    home_path: Path = Path.home() / '.colusa',
) -> Config:
    """Load and merge ~/.colusa and .colusa into a Config. Project values override home values."""
    home_raw = _load_file(home_path)
    project_raw = _load_file(project_path)

    # Scalar merge: project overrides home
    def _pick(key: str):
        if key in project_raw:
            return project_raw[key]
        return home_raw.get(key)

    ssl_cert = _pick('ssl_cert')
    doh = _pick('doh')
    browser = _pick('browser') or False

    cache_dir_raw = _pick('cache_dir')
    cache_dir = Path(cache_dir_raw).expanduser() if cache_dir_raw else None

    # Site rules: project first (higher priority in specificity sort)
    project_rules = _parse_site_rules(project_raw)
    home_rules = _parse_site_rules(home_raw)
    sites = project_rules + home_rules

    return Config(
        ssl_cert=ssl_cert,
        cache_dir=cache_dir,
        doh=doh,
        browser=browser,
        sites=sites,
    )


def _wildcard_count(pattern: str) -> int:
    """Count wildcard characters (* and ?) in a glob pattern."""
    return pattern.count('*') + pattern.count('?')


def match_site_rule(url: str, sites: list[tuple[str, SiteRule]]) -> SiteRule | None:
    """Match URL hostname against configured glob patterns. Returns best (most specific) match."""
    hostname = urlparse(url).hostname or ''
    sorted_sites = sorted(sites, key=lambda item: _wildcard_count(item[0]))
    for pattern, rule in sorted_sites:
        if fnmatch.fnmatch(hostname, pattern):
            return rule
    return None
