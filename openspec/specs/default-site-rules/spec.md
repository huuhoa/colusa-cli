# Spec: Default Site Rules

## Purpose

TBD — Define how colusa-cli bundles and loads a curated set of default site rules shipped as package data.

## Requirements

### Requirement: Bundled default site rules ship as package data
The package SHALL include a `defaults.toml` file at `src/colusa_cli/defaults.toml` containing curated site rules. This file SHALL be declared as package data in `pyproject.toml` so it is included in built wheels and editable installs.

#### Scenario: File present after install
- **WHEN** `colusa-cli` is installed via pip
- **THEN** `importlib.resources.files('colusa_cli').joinpath('defaults.toml')` resolves to a readable file

#### Scenario: File present in editable install
- **WHEN** `colusa-cli` is installed with `pip install -e .`
- **THEN** the defaults file is accessible via `importlib.resources` without error

### Requirement: Default rules are loaded at runtime via importlib.resources
The system SHALL read `defaults.toml` using `importlib.resources.files('colusa_cli').joinpath('defaults.toml').read_bytes()` and parse it with `tomllib`. No file is written to the user's home directory.

#### Scenario: Defaults loaded without any user config
- **WHEN** neither `~/.colusa` nor `.colusa` exists
- **THEN** the bundled default rules are active and site-specific extraction works for covered hostnames

#### Scenario: Defaults load silently
- **WHEN** the tool starts
- **THEN** no message about defaults is printed to stdout or stderr

### Requirement: Default rules cover approximately 40 popular sites
The `defaults.toml` SHALL contain rules for at least 40 commonly-used websites, with accurate `content` CSS selectors verified against current site markup.

#### Scenario: Known site uses default rule
- **WHEN** a URL from a site covered in `defaults.toml` is fetched
- **THEN** `quality: full-article` is returned (not `body-fallback`)
