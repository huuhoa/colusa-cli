## Why

colusa-cli currently requires SSL certificates and site-specific CSS selectors to be passed as CLI flags or environment variables on every invocation, which is tedious for repeated use and makes per-site extraction rules impossible to persist. A configuration file allows users to capture these settings once and have them applied automatically.

## What Changes

- New `.colusa` TOML configuration file loaded at startup (current directory, then `~/.colusa`)
- Both files merged when present: project-level overrides home-level for scalar settings; site rules from both are combined
- Per-site extraction rules: map URL hostname glob patterns to CSS selectors, cleanup rules, and browser mode
- Specificity-sorted pattern matching: more specific patterns (fewer wildcards) take precedence
- New `--ssl-cert` CLI flag to explicitly set the SSL certificate file
- `SiteRule` gains a `browser` field enabling per-site automatic headless browser fetch

## Capabilities

### New Capabilities

- `config-loading`: Discover, parse, and merge `.colusa` TOML files from project and home directories into a unified `Config` object
- `site-rule-matching`: Match a URL's hostname against configured glob patterns using specificity-sorted fnmatch, returning the best-matching `SiteRule`

### Modified Capabilities

- `cli-entrypoint`: CLI gains `--ssl-cert` flag; config values become defaults that CLI flags override; resolved settings are wired to `Downloader` and `Extractor`

## Impact

- **New file**: `src/colusa_cli/config.py`
- **Modified**: `src/colusa_cli/etr.py` — `SiteRule` adds `browser: bool = False`
- **Modified**: `src/colusa_cli/cli.py` — config loading, `--ssl-cert` flag, site rule matching, per-site browser trigger
- **Modified**: `src/colusa_cli/fetch.py` — `Downloader` accepts explicit `ssl_cert` parameter
- **No new dependencies** — uses stdlib `tomllib` (Python 3.11+) and `fnmatch`
