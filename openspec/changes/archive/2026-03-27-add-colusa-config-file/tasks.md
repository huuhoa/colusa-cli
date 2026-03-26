## 1. Data Model

- [x] 1.1 Add `browser: bool = False` field to `SiteRule` dataclass in `etr.py`
- [x] 1.2 Create `Config` dataclass in new `src/colusa_cli/config.py` with fields: `ssl_cert: str | None`, `cache_dir: Path | None`, `doh: str | None`, `browser: bool`, `sites: list[tuple[str, SiteRule]]`

## 2. Config Loading

- [x] 2.1 Implement `_load_file(path: Path) -> dict` in `config.py` — parse TOML, catch `TOMLDecodeError` and raise with file path context, return empty dict if file missing
- [x] 2.2 Implement `_parse_site_rules(raw: dict, priority: int) -> list[tuple[str, int, SiteRule]]` — extract `[sites.*]` tables into `(pattern, priority, SiteRule)` tuples
- [x] 2.3 Implement `load_config(project_path: Path = Path(".colusa"), home_path: Path = Path.home() / ".colusa") -> Config` — load home then project path, merge scalars (project overrides home), concatenate site rules (project first)

## 3. Site Rule Matching

- [x] 3.1 Implement `_wildcard_count(pattern: str) -> int` helper — count `*` and `?` characters
- [x] 3.2 Implement `match_site_rule(url: str, sites: list[tuple[str, SiteRule]]) -> SiteRule | None` — extract hostname via `urllib.parse.urlparse`, sort by wildcard count ascending, return first `fnmatch` match

## 4. Downloader SSL Wiring

- [x] 4.1 Add `ssl_cert: str | None = None` parameter to `Downloader.__init__`
- [x] 4.2 Update `Downloader.fetch` to use `self.ssl_cert` when resolving the `verify` argument (before falling back to `ssl.get_default_verify_paths()`)

## 5. CLI Integration

- [x] 5.1 Add `--ssl-cert` argument to `argparse` in `cli.py`
- [x] 5.2 Call `load_config()` at the start of `main()`, wrap in try/except to print error and exit 1 on config parse failure
- [x] 5.3 Resolve final scalar settings: CLI flag → config value → env var → system default (for ssl_cert); CLI flag → config value → default (for cache_dir, doh, browser)
- [x] 5.4 Call `match_site_rule(args.url, config.sites)` to get matched rule; use `DynamicExtractor` if rule found (merging with `--selector` if also provided — CLI selector overrides rule's content field)
- [x] 5.5 If matched rule has `browser = True` (and `--browser` not already set), set browser mode before fetch
- [x] 5.6 Pass resolved `ssl_cert` and `cache_dir` to `Downloader`

## 6. Tests

Use pytest throughout. Pass `tmp_path / ".colusa"` directly to `load_config(project_path=..., home_path=...)` — no monkeypatching needed. For CLI tests, call `main()` via `pytest`'s `monkeypatch` + `capsys`, or use `unittest.mock.patch` to intercept `Downloader` and browser module calls.

- [x] 6.1 Test `load_config(project_path, home_path)` with no files, home only, project only, and both files present — pass `tmp_path`-based paths
- [x] 6.2 Test merge: project scalar overrides home; site rules concatenated with project first
- [x] 6.3 Test malformed TOML: `load_config()` raises with a message containing the file path
- [x] 6.4 Test `match_site_rule` — exact match, wildcard match, no match, specificity ordering (exact beats wildcard)
- [x] 6.5 Test `--ssl-cert` CLI flag: mock `Downloader.__init__` and assert `ssl_cert` param is set correctly
- [x] 6.6 Test per-site `browser = true`: mock browser module and assert it is called when matched site rule has `browser = True`
