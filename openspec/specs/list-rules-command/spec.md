# Spec: List Rules Command

## Purpose

TBD — Define the `--list-rules` CLI flag that prints the merged active rule set and exits.

## Requirements

### Requirement: --list-rules flag prints all active rules and exits
The CLI SHALL support a `--list-rules` flag. When provided, it SHALL print the merged active rule set as a table and exit with code 0, without fetching any URL.

#### Scenario: Flag without URL argument
- **WHEN** `colusa-cli --list-rules` is run with no URL
- **THEN** the table is printed and the process exits 0

#### Scenario: Flag overrides URL processing
- **WHEN** `colusa-cli --list-rules <url>` is run with a URL
- **THEN** the table is printed and the URL is not fetched

### Requirement: Rule table columns are PATTERN, CONTENT, SOURCE
The output table SHALL have three columns: `PATTERN` (the glob string), `CONTENT` (the content CSS selector, or empty string if not set), and `SOURCE` (one of `[default]`, `[~/.colusa]`, `[.colusa]`). Rows SHALL be printed in priority order: project rules first, then home rules, then default rules.

#### Scenario: Mixed sources
- **WHEN** rules exist in `defaults.toml`, `~/.colusa`, and `.colusa`
- **THEN** the table shows all rules with correct SOURCE tags, project rules at the top

#### Scenario: No user config, only defaults
- **WHEN** neither `~/.colusa` nor `.colusa` exists
- **THEN** only default rules are listed, each tagged `[default]`

#### Scenario: Empty rule set
- **WHEN** no rules exist in any source (empty defaults and no user config)
- **THEN** an empty table or a "no rules configured" message is printed
