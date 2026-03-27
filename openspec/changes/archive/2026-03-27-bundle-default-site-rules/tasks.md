## 1. Package Data Setup

- [x] 1.1 Add `[tool.setuptools.package-data]` to `pyproject.toml` declaring `colusa_cli = ["*.toml"]`
- [x] 1.2 Create `src/colusa_cli/defaults.toml` with TOML structure and ~40 curated site rules

## 2. Config Loading

- [x] 2.1 Add `_load_defaults()` to `config.py` using `importlib.resources.files('colusa_cli').joinpath('defaults.toml').read_bytes()`
- [x] 2.2 Update `load_config()` to parse default rules and prepend them as the lowest-priority layer: `default_rules + home_rules + project_rules`
- [x] 2.3 Extend the `Config` dataclass or `load_config()` return to track source per rule (needed for `--list-rules`)

## 3. CLI --list-rules Flag

- [x] 3.1 Add `--list-rules` argument to the argparse parser in `cli.py`
- [x] 3.2 Implement the handler: load config, format rules as a table (PATTERN, CONTENT, SOURCE), print and exit 0
- [x] 3.3 Ensure `--list-rules` works without a URL argument (URL should be optional when this flag is present)

## 4. Tests

- [x] 4.1 Test that `_load_defaults()` returns parsed rules from the bundled file
- [x] 4.2 Test `load_config()` merge order: project rules shadow home rules shadow defaults
- [x] 4.3 Test `--list-rules` output includes correct SOURCE tags for each layer
