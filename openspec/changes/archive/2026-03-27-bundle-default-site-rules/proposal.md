## Why

Users must discover and hand-author all site rules themselves; there are no bundled starting rules. Shipping ~40 curated defaults as package data means users get working extraction out of the box, and improvements in new releases benefit everyone automatically.

## What Changes

- Add `src/colusa_cli/defaults.toml` containing ~40 site rules, shipped as package data
- Load bundled defaults as the lowest-priority config layer (below `~/.colusa` and `.colusa`)
- Add `--list-rules` CLI flag that prints all active rules in a table (pattern, content selector, source tag)
- Update `pyproject.toml` to declare `*.toml` as package data so the file is included in wheels

## Capabilities

### New Capabilities
- `default-site-rules`: Bundled TOML file of curated site rules loaded at runtime via `importlib.resources`
- `list-rules-command`: CLI flag `--list-rules` that prints the merged active rule set with source attribution

### Modified Capabilities
- `config-loading`: Config load order gains a new lowest-priority layer (bundled defaults beneath `~/.colusa`)

## Impact

- `src/colusa_cli/config.py` — `load_config()` gains a third source
- `src/colusa_cli/cli.py` — new `--list-rules` argument and handler
- `pyproject.toml` — `[tool.setuptools.package-data]` addition
- New file: `src/colusa_cli/defaults.toml`
- No breaking changes; existing `~/.colusa` and `.colusa` rules continue to override defaults
