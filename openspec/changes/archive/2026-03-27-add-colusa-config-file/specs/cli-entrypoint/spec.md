## ADDED Requirements

### Requirement: CLI accepts --ssl-cert flag to specify SSL certificate file
The system SHALL accept a `--ssl-cert` CLI flag that specifies the path to a CA bundle file for HTTPS verification. This flag takes the highest priority in the SSL cert resolution chain.

#### Scenario: --ssl-cert flag overrides all other ssl_cert sources
- **WHEN** `--ssl-cert /path/to/cert.pem` is passed and `~/.colusa` also sets `ssl_cert`
- **THEN** `/path/to/cert.pem` is used for SSL verification

#### Scenario: SSL cert priority chain
- **WHEN** no `--ssl-cert` flag is given
- **THEN** the system checks config file `ssl_cert`, then `SSL_CERT_FILE` env var, then `ssl.get_default_verify_paths().cafile`, then falls back to `True` (requests default)

### Requirement: Config file values serve as defaults overridable by CLI flags
The system SHALL load config at startup and use config values as defaults. Any CLI flag explicitly provided by the user SHALL override the corresponding config value.

#### Scenario: CLI cache-dir overrides config cache_dir
- **WHEN** config sets `cache_dir = "~/.cache/colusa-cli"` and `--cache-dir /tmp/cache` is passed
- **THEN** `/tmp/cache` is used as the cache directory

#### Scenario: Config doh applied when no --doh flag given
- **WHEN** config sets `doh = "cloudflare"` and no `--doh` flag is passed
- **THEN** Cloudflare DoH is enabled automatically

### Requirement: Matched site rule is applied automatically without --selector flag
The system SHALL match the target URL against configured site rules before extraction. If a rule is found, it SHALL be applied as if `--selector` and related options were specified, without the user needing to pass any flags.

#### Scenario: Site rule applied automatically
- **WHEN** a site rule for `*.medium.com` is configured with `content = ".story-body"` and the URL is a medium.com article
- **THEN** `.story-body` is used for content extraction without any CLI flags

#### Scenario: --selector flag overrides config site rule
- **WHEN** a config site rule exists for the URL and `--selector ".custom"` is also passed
- **THEN** `.custom` takes precedence over the config rule's content selector

### Requirement: Per-site browser flag triggers automatic headless fetch
The system SHALL automatically use headless browser fetch for URLs whose matched site rule has `browser = true`, without requiring the `--browser` CLI flag.

#### Scenario: Per-site browser mode triggered by config
- **WHEN** a site rule for `*.substack.com` has `browser = true` and a substack.com URL is fetched
- **THEN** the headless browser is used for fetching, not the HTTP client
