## ADDED Requirements

### Requirement: Discover and load config files from standard locations
The system SHALL search for `.colusa` config files in two locations: the current working directory and the user's home directory (`~/.colusa`). Both files are in TOML format. A missing file is silently ignored. A malformed file SHALL cause an error message to stderr and exit with code 1.

#### Scenario: Only home config exists
- **WHEN** `~/.colusa` exists and `.colusa` does not exist in the current directory
- **THEN** the home config is loaded and its settings are applied

#### Scenario: Only project config exists
- **WHEN** `.colusa` exists in the current directory and `~/.colusa` does not exist
- **THEN** the project config is loaded and its settings are applied

#### Scenario: Neither config file exists
- **WHEN** neither `.colusa` nor `~/.colusa` exists
- **THEN** the tool runs with built-in defaults and no error is raised

#### Scenario: Config file is malformed TOML
- **WHEN** a `.colusa` file exists but contains invalid TOML
- **THEN** the tool prints an error message identifying the file path and exits with code 1

### Requirement: Merge configs with project taking precedence for scalar settings
When both `~/.colusa` and `.colusa` exist, the system SHALL merge them. For scalar settings (`ssl_cert`, `cache_dir`, `doh`, `browser`), the project-level value overrides the home-level value. A setting absent from the project config falls back to the home config value.

#### Scenario: Project overrides home scalar
- **WHEN** both files set `cache_dir` to different values
- **THEN** the project-level `cache_dir` is used

#### Scenario: Project inherits unset home scalar
- **WHEN** `~/.colusa` sets `ssl_cert` and `.colusa` does not mention `ssl_cert`
- **THEN** the `ssl_cert` from `~/.colusa` is used

### Requirement: Config file contains a format comment header
The system SHALL use `# colusa-cli configuration (TOML format — https://toml.io)` as the recommended first line in documentation and generated config examples, so users who encounter an unfamiliar `.colusa` file can identify its format.

#### Scenario: Comment in example docs
- **WHEN** a user reads documentation or a sample `.colusa` file
- **THEN** the first line identifies the file as TOML format

### Requirement: Config supports site rule tables keyed by hostname glob pattern
The config file SHALL allow site-specific rules under `[sites."<pattern>"]` TOML tables, where `<pattern>` is a glob string matched against URL hostnames. Each site table may contain `content`, `title`, `author`, `published`, `cleanup`, and `browser` fields mirroring `SiteRule`.

#### Scenario: Single site rule in config
- **WHEN** the config contains `[sites."*.medium.com"]` with `content = ".story-body"`
- **THEN** fetching any medium.com URL uses `.story-body` as the content selector

#### Scenario: Site table with cleanup list
- **WHEN** a site table specifies `cleanup = [".sidebar", ".ads"]`
- **THEN** those elements are removed from the extracted content

#### Scenario: Site table with browser flag
- **WHEN** a site table specifies `browser = true`
- **THEN** fetching that site automatically uses headless browser mode
