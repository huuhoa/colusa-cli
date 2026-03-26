# Spec: Site Rule Matching

## Purpose

Define how colusa-cli matches a request URL against configured site rules using hostname glob patterns, including specificity-based ordering and project-over-home precedence.

## Requirements

### Requirement: Match URL hostname against configured glob patterns
The system SHALL extract the hostname from a given URL and test it against all configured site patterns using `fnmatch` glob matching. The system SHALL return the `SiteRule` for the first matching pattern after specificity sorting.

#### Scenario: Exact hostname match
- **WHEN** the URL is `https://docs.python.org/3/library/` and a pattern `docs.python.org` is configured
- **THEN** that pattern's `SiteRule` is returned

#### Scenario: Wildcard subdomain match
- **WHEN** the URL is `https://username.substack.com/p/article` and a pattern `*.substack.com` is configured
- **THEN** that pattern's `SiteRule` is returned

#### Scenario: No pattern matches
- **WHEN** no configured pattern matches the URL hostname
- **THEN** `None` is returned and the auto-detection extractor is used

### Requirement: Sort patterns by specificity before matching
The system SHALL sort all configured site patterns in ascending order of wildcard character count (`*` and `?`) before testing. Patterns with fewer wildcards are tested first and take precedence.

#### Scenario: Exact pattern beats wildcard pattern
- **WHEN** both `docs.python.org` and `*.python.org` are configured
- **THEN** a URL with hostname `docs.python.org` matches `docs.python.org` not `*.python.org`

#### Scenario: Single-wildcard pattern beats catch-all
- **WHEN** both `*.medium.com` and `*` are configured
- **THEN** a URL with hostname `medium.com` matches `*.medium.com` not `*`

### Requirement: Project-level rules take precedence over home-level rules within equal specificity
When patterns from the project `.colusa` and home `~/.colusa` have equal wildcard counts, project-level patterns SHALL be tested before home-level patterns.

#### Scenario: Project rule overrides home rule of same specificity
- **WHEN** both `~/.colusa` and `.colusa` define a rule for `*.medium.com`
- **THEN** the project-level rule is used for medium.com URLs
