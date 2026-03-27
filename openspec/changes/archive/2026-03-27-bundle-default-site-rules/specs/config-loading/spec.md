## MODIFIED Requirements

### Requirement: Discover and load config files from standard locations
The system SHALL search for `.colusa` config files in three locations: the package-bundled `defaults.toml`, the user's home directory (`~/.colusa`), and the current working directory (`.colusa`). All files are in TOML format. A missing user config file is silently ignored. A malformed file SHALL cause an error message to stderr and exit with code 1. The bundled defaults file is always present and cannot be missing.

#### Scenario: Only home config exists
- **WHEN** `~/.colusa` exists and `.colusa` does not exist in the current directory
- **THEN** the home config is loaded and its settings are applied

#### Scenario: Only project config exists
- **WHEN** `.colusa` exists in the current directory and `~/.colusa` does not exist
- **THEN** the project config is loaded and its settings are applied

#### Scenario: Neither user config file exists
- **WHEN** neither `.colusa` nor `~/.colusa` exists
- **THEN** the tool runs using only bundled defaults and no error is raised

#### Scenario: Config file is malformed TOML
- **WHEN** a `.colusa` file exists but contains invalid TOML
- **THEN** the tool prints an error message identifying the file path and exits with code 1

## ADDED Requirements

### Requirement: Bundled defaults are the lowest-priority config layer
The system SHALL load site rules from the bundled `defaults.toml` as the lowest-priority layer. Site rules are merged in order: default rules (lowest), then home rules, then project rules (highest). For scalar settings, bundled defaults have no effect — only `~/.colusa` and `.colusa` supply scalar values.

#### Scenario: User rule overrides default rule for same pattern
- **WHEN** `defaults.toml` and `~/.colusa` both define a rule for `github.com`
- **THEN** the `~/.colusa` rule is matched first (higher priority)

#### Scenario: Default rule used when no user rule matches
- **WHEN** a URL matches a pattern in `defaults.toml` but no pattern in `~/.colusa` or `.colusa`
- **THEN** the bundled default rule is applied
