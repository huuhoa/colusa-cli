## Context

colusa-cli is a single-command CLI tool that fetches URLs and converts them to Markdown. Currently all runtime settings (SSL cert, cache directory, CSS selectors) must be provided as CLI flags or environment variables on every invocation. There is no persistence layer.

The codebase uses `SiteRule` + `DynamicExtractor` in `etr.py` for CSS-selector-driven extraction — that mechanism already works and just needs a config-driven way to supply rules automatically.

## Goals / Non-Goals

**Goals:**
- Load `.colusa` TOML config from current directory and/or `~/.colusa`, merging both
- Match URL hostnames against glob patterns to automatically apply site-specific `SiteRule`s
- Add `--ssl-cert` CLI flag; wire resolved ssl_cert into `Downloader`
- Per-site `browser = true` automatically triggers headless fetch for matched sites
- Zero new third-party dependencies (use stdlib `tomllib`, `fnmatch`, `pathlib`)

**Non-Goals:**
- Per-site DoH override (DoH patches the global DNS resolver; per-connection scoping is not feasible)
- Config file creation/editing commands (out of scope for this change)
- Validation of config file schema beyond what's needed for correct operation

## Decisions

### Decision: TOML format with `tomllib` (stdlib)

**Chosen**: TOML via Python 3.11+ `tomllib`.

**Rationale**: TOML is already used in the project (`pyproject.toml`). `tomllib` is stdlib since 3.11, so no new dependency. TOML handles nested tables cleanly for the `[sites."*.medium.com"]` pattern. The header comment `# colusa-cli configuration (TOML format — https://toml.io)` makes the format self-documenting.

**Alternative considered**: YAML — more flexible but requires `pyyaml` dependency and is prone to surprising parsing edge cases.

### Decision: Specificity sort by wildcard count

**Chosen**: Sort patterns by ascending wildcard character count (`*` and `?`) before matching. First match wins. Within equal specificity, project-file rules come before home-file rules.

**Rationale**: Users naturally expect `docs.python.org` to beat `*.python.org`. Explicit sort makes the behavior deterministic and independent of file ordering. Wildcard count is a simple, understandable proxy for specificity.

**Alternative considered**: Order-of-appearance only — simpler but requires users to manually order rules, which is error-prone across two merged files.

### Decision: `load_config()` accepts injectable paths for testability

**Chosen**: `load_config()` accepts optional path parameters with production defaults:

```python
def load_config(
    project_path: Path = Path(".colusa"),
    home_path: Path = Path.home() / ".colusa",
) -> Config: ...
```

**Rationale**: The function discovers files at fixed filesystem locations, which makes it untestable without controlling those paths. Injectable parameters keep the function pure (no global state, no monkeypatching needed) and let tests pass `tmp_path / ".colusa"` directly. Production callers use the defaults and need no changes.

**Alternative considered**: `monkeypatch.chdir()` + `monkeypatch.setenv("HOME", ...)` in tests — works but couples tests to OS-level state and makes test intent less clear.

### Decision: Merge strategy — concatenate site rules, project scalars override home

**Chosen**: Scalar settings (`ssl_cert`, `cache_dir`, `doh`, `browser`) — project file value wins if present, else home file value. Site rules — concatenated, project rules appended first (higher priority in specificity-sorted matching).

**Rationale**: Home `~/.colusa` acts as a personal library of site rules; project `.colusa` adds or overrides for the specific project context. Users rarely need to completely suppress a home rule — they just add a more-specific one.

### Decision: `browser` as a field on `SiteRule`

**Chosen**: Add `browser: bool = False` to `SiteRule` dataclass in `etr.py`.

**Rationale**: `SiteRule` already bundles all per-site extraction configuration. The `browser` flag is logically per-site (some sites always need headless fetch). Adding it here keeps all per-site config in one place and flows naturally to the existing `DynamicExtractor` path in `cli.py`.

### Decision: SSL cert priority chain

```
--ssl-cert CLI flag
  ↓ config file ssl_cert
  ↓ SSL_CERT_FILE env var
  ↓ ssl.get_default_verify_paths().cafile
  ↓ True (requests default)
```

**Rationale**: CLI flag is always highest priority (user intent). Config is persistent preference. Env var preserves existing `SSL_CERT_FILE=... colusa-cli` workflow. System paths are the final fallback.

## Risks / Trade-offs

- **`tomllib` requires Python 3.11+** → `pyproject.toml` already targets 3.11+; not a new constraint. For older Pythons, `tomllib` is available as `tomli` on PyPI but we don't need to support that.
- **Silent config file errors** → A malformed `.colusa` file will raise a `TOMLDecodeError`. We should catch it, print a clear error with the file path, and exit 1. A missing file is silently ignored (expected).
- **Wildcard count as specificity proxy is imperfect** → `*.com` and `*.medium.com` both have one `*`, so same specificity. Within-same-specificity ordering (project before home) will resolve most real cases. Edge cases are acceptable at this scope.

## Migration Plan

No migration needed. The config file is optional; existing CLI-flag-only usage is unaffected. The `--ssl-cert` flag is additive. `SiteRule.browser` defaults to `False`, preserving current behavior.
