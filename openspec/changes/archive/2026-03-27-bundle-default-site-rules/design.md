## Context

`config.py:load_config()` currently reads two TOML files (`~/.colusa`, `.colusa`) and merges them. Site rules are accumulated as `project_rules + home_rules` and sorted by specificity at match time. The `SiteRule` dataclass has fields: `content`, `title`, `author`, `published`, `cleanup`, `browser`.

The package is built with setuptools from `src/`. Python version requirement is >=3.9, so `importlib.resources.files()` (stable since 3.9) is available without backports.

## Goals / Non-Goals

**Goals:**
- Load bundled defaults as the third (lowest-priority) config layer at runtime
- Never write files to the user's home directory
- Defaults automatically improve when users upgrade the package
- Users can inspect the full merged rule set with source attribution

**Non-Goals:**
- Writing or managing files in `~/.colusa` — that stays entirely user-controlled
- A separate `~/.colusa.d/` drop-in directory mechanism
- Merging or diffing bundled defaults with user rules at a per-field level

## Decisions

### 1. Runtime read via `importlib.resources`, not file copy on install

**Decision**: Read `defaults.toml` from the package at load time using `importlib.resources.files('colusa_cli').joinpath('defaults.toml').read_bytes()`.

**Rationale**: Avoids post-install hooks (unreliable with pip), avoids writing to user home, and means upgrades are transparent — the user never needs to re-run any init command.

**Alternative considered**: `colusa-cli init` command that copies defaults to `~/.colusa` on first run. Rejected because it makes upgrades awkward (would need to merge, not overwrite) and complicates the mental model.

### 2. Merge order: `default_rules + home_rules + project_rules`

**Decision**: Bundled defaults are appended last in the list passed to specificity sort, so any user rule for the same pattern wins by appearing earlier.

**Rationale**: Consistent with the existing `project_rules + home_rules` precedence model. The specificity sort (`_wildcard_count`) already handles tiebreaking; putting user rules first ensures they are tried first among equal-specificity patterns.

### 3. `--list-rules` output: flat table with source column

**Decision**: Print one row per rule, columns: `PATTERN`, `CONTENT`, `SOURCE`. Source values: `[default]`, `[~/.colusa]`, `[.colusa]`. Rules printed in priority order (project first, defaults last).

**Rationale**: Option A selected by the user. Easy to scan, shows exactly what is active and where it came from. No TOML output needed for this flag.

### 4. Package data declaration in `pyproject.toml`

**Decision**: Add `[tool.setuptools.package-data]` with `colusa_cli = ["*.toml"]`.

**Rationale**: setuptools does not auto-include non-`.py` files without explicit declaration. This is the minimal, standard way to ensure `defaults.toml` ships in the wheel.

## Risks / Trade-offs

- **Defaults file grows large**: ~40 rules is small; no performance concern. If it reaches hundreds, consider lazy loading — not needed now.
- **Rule conflicts with user customizations**: Silently shadowed by user rules (correct behavior), but may be surprising if a user's rule is less specific. The `--list-rules` output makes this visible.
- **`importlib.resources` edge cases in editable installs**: `files()` works correctly with `pip install -e` as long as the file is present in the source tree. No issue expected.

## Migration Plan

No migration needed. Existing `~/.colusa` and `.colusa` files are unaffected. The new defaults layer is additive and lowest-priority.
