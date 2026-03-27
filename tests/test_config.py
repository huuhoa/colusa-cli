import pytest
from pathlib import Path

from colusa_cli.config import ConfigError, _load_defaults, load_config, match_site_rule
from colusa_cli.etr import SiteRule


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def write_toml(path: Path, content: str) -> Path:
    path.write_text(content, encoding='utf-8')
    return path


ABSENT = Path('/nonexistent/does/not/exist/.colusa')


# ---------------------------------------------------------------------------
# Task 6.1: load_config with no files, home only, project only, both present
# ---------------------------------------------------------------------------

def test_load_config_no_files():
    config = load_config(project_path=ABSENT, home_path=ABSENT, _defaults_raw={})
    assert config.ssl_cert is None
    assert config.cache_dir is None
    assert config.doh is None
    assert config.browser is False
    assert config.sites == []


def test_load_config_home_only(tmp_path):
    home = write_toml(tmp_path / 'home.colusa', 'ssl_cert = "/home/cert.pem"\n')
    config = load_config(project_path=ABSENT, home_path=home, _defaults_raw={})
    assert config.ssl_cert == '/home/cert.pem'


def test_load_config_project_only(tmp_path):
    project = write_toml(tmp_path / 'proj.colusa', 'cache_dir = "/tmp/cache"\n')
    config = load_config(project_path=project, home_path=ABSENT, _defaults_raw={})
    assert config.cache_dir == Path('/tmp/cache')


def test_load_config_both_files(tmp_path):
    home = write_toml(tmp_path / 'home.colusa', 'ssl_cert = "/home/cert.pem"\ndoh = "cloudflare"\n')
    project = write_toml(tmp_path / 'proj.colusa', 'doh = "google"\n')
    config = load_config(project_path=project, home_path=home, _defaults_raw={})
    assert config.ssl_cert == '/home/cert.pem'   # from home (not in project)
    assert config.doh == 'google'                # project overrides home


# ---------------------------------------------------------------------------
# Task 6.2: merge — project scalar overrides home; site rules concatenated
# ---------------------------------------------------------------------------

def test_merge_project_scalar_overrides_home(tmp_path):
    home = write_toml(tmp_path / 'h', 'ssl_cert = "/home/cert.pem"\ncache_dir = "/home/cache"\n')
    project = write_toml(tmp_path / 'p', 'ssl_cert = "/project/cert.pem"\n')
    config = load_config(project_path=project, home_path=home, _defaults_raw={})
    assert config.ssl_cert == '/project/cert.pem'
    assert str(config.cache_dir) == '/home/cache'   # home fallback


def test_merge_site_rules_project_first(tmp_path):
    home = write_toml(tmp_path / 'h', '[sites."*.home.com"]\ncontent = ".home-body"\n')
    project = write_toml(tmp_path / 'p', '[sites."*.proj.com"]\ncontent = ".proj-body"\n')
    config = load_config(project_path=project, home_path=home, _defaults_raw={})
    patterns = [p for p, _, _ in config.sites]
    assert patterns.index('*.proj.com') < patterns.index('*.home.com')


# ---------------------------------------------------------------------------
# Task 6.3: malformed TOML raises ConfigError with file path
# ---------------------------------------------------------------------------

def test_malformed_toml_raises(tmp_path):
    bad = write_toml(tmp_path / 'bad.colusa', 'this is not = [valid toml\n')
    with pytest.raises(ConfigError) as exc_info:
        load_config(project_path=bad, home_path=ABSENT)
    assert str(bad) in str(exc_info.value)


# ---------------------------------------------------------------------------
# Task 6.4: match_site_rule — exact, wildcard, no match, specificity order
# ---------------------------------------------------------------------------

def test_match_exact():
    rule = SiteRule(content='.exact')
    sites = [('docs.python.org', rule, '[default]')]
    assert match_site_rule('https://docs.python.org/3/', sites) is rule


def test_match_wildcard():
    rule = SiteRule(content='.wild')
    sites = [('*.medium.com', rule, '[default]')]
    assert match_site_rule('https://user.medium.com/article', sites) is rule


def test_match_no_match():
    sites = [('*.medium.com', SiteRule(), '[default]')]
    assert match_site_rule('https://example.com/page', sites) is None


def test_match_specificity_exact_beats_wildcard():
    exact_rule = SiteRule(content='.exact')
    wild_rule = SiteRule(content='.wild')
    # exact pattern has 0 wildcards, wildcard pattern has 1 — exact should win
    sites = [('*.python.org', wild_rule, '[default]'), ('docs.python.org', exact_rule, '[default]')]
    result = match_site_rule('https://docs.python.org/3/', sites)
    assert result is exact_rule


def test_match_specificity_equal_wildcard_count_uses_list_order():
    # '*' and '*.medium.com' both have 1 wildcard — same specificity.
    # List order determines the winner (project rules are placed first during merge).
    first = SiteRule(content='.first')
    second = SiteRule(content='.second')
    sites = [('*.medium.com', first, '[.colusa]'), ('*', second, '[default]')]
    result = match_site_rule('https://user.medium.com/article', sites)
    assert result is first


def test_match_specificity_fewer_wildcards_beats_more():
    # '*.medium.com' (1 wildcard) beats '*.*' (2 wildcards)
    specific = SiteRule(content='.specific')
    vague = SiteRule(content='.vague')
    sites = [('*.*', vague, '[default]'), ('*.medium.com', specific, '[default]')]
    result = match_site_rule('https://user.medium.com/article', sites)
    assert result is specific


# ---------------------------------------------------------------------------
# Task 6.5: --ssl-cert CLI flag wires through to Downloader
# ---------------------------------------------------------------------------

def test_cli_ssl_cert_flag(tmp_path, monkeypatch):
    from unittest.mock import patch
    from colusa_cli.config import Config
    import colusa_cli.cli as cli_mod

    captured = {}

    def mock_init(self, cache_dir=None, ssl_cert=None):
        captured['ssl_cert'] = ssl_cert
        self.cache_dir = tmp_path
        self.ssl_cert = ssl_cert

    def mock_fetch(self, url, no_cache=False):
        return '<html><body><article>content</article></body></html>'

    monkeypatch.setattr(cli_mod.Downloader, '__init__', mock_init)
    monkeypatch.setattr(cli_mod.Downloader, 'fetch', mock_fetch)
    monkeypatch.setattr('sys.argv', ['colusa-cli', '--ssl-cert', '/my/cert.pem', 'https://example.com/'])

    with patch.object(cli_mod, 'load_config', return_value=Config()):
        try:
            cli_mod.main()
        except SystemExit:
            pass

    assert captured.get('ssl_cert') == '/my/cert.pem'


# ---------------------------------------------------------------------------
# Task 6.6: per-site browser=True triggers browser fetch
# ---------------------------------------------------------------------------

def test_per_site_browser_triggers_browser_fetch(monkeypatch):
    from unittest.mock import patch
    from colusa_cli.config import Config
    import colusa_cli.cli as cli_mod
    import colusa_cli.browser as browser_module

    browser_called = []

    def mock_browser_fetch(url):
        browser_called.append(url)
        return '<html><body><article>content</article></body></html>'

    site_rule = SiteRule(content='.body', browser=True)

    monkeypatch.setattr('sys.argv', ['colusa-cli', 'https://sub.substack.com/p/article'])
    monkeypatch.setattr(browser_module, 'fetch', mock_browser_fetch)

    with patch.object(cli_mod, 'load_config', return_value=Config()), \
         patch.object(cli_mod, 'match_site_rule', return_value=site_rule):
        try:
            cli_mod.main()
        except SystemExit:
            pass

    assert len(browser_called) > 0
    assert browser_called[0] == 'https://sub.substack.com/p/article'


# ---------------------------------------------------------------------------
# New: bundled defaults, merge order, --list-rules
# ---------------------------------------------------------------------------

def test_load_defaults_returns_site_rules():
    raw = _load_defaults()
    sites = raw.get('sites', {})
    assert len(sites) >= 40, f'Expected at least 40 bundled rules, got {len(sites)}'
    # Spot-check a known rule
    assert 'github.com' in sites
    assert sites['github.com'].get('content'), 'github.com rule should have a content selector'


def test_merge_order_defaults_lowest_priority(tmp_path):
    # A home rule for the same pattern should shadow the default
    home = write_toml(tmp_path / 'h', '[sites."github.com"]\ncontent = ".custom-body"\n')
    config = load_config(project_path=ABSENT, home_path=home)
    patterns_sources = [(p, s) for p, _, s in config.sites]
    # Home rule for github.com must appear before the default rule
    home_idx = next(i for i, (p, s) in enumerate(patterns_sources) if p == 'github.com' and s == '[~/.colusa]')
    default_idx = next(i for i, (p, s) in enumerate(patterns_sources) if p == 'github.com' and s == '[default]')
    assert home_idx < default_idx


def test_list_rules_output(monkeypatch, capsys):
    from unittest.mock import patch
    from colusa_cli.config import Config
    from colusa_cli.etr import SiteRule as SR
    import colusa_cli.cli as cli_mod

    fake_config = Config(sites=[
        ('proj-site.com', SR(content='.article'), '[.colusa]'),
        ('my-site.com', SR(content='.post'), '[~/.colusa]'),
        ('github.com', SR(content='.markdown-body'), '[default]'),
    ])

    monkeypatch.setattr('sys.argv', ['colusa-cli', '--list-rules'])

    with patch.object(cli_mod, 'load_config', return_value=fake_config):
        try:
            cli_mod.main()
        except SystemExit:
            pass

    out = capsys.readouterr().out
    assert 'PATTERN' in out
    assert 'SOURCE' in out
    assert '[.colusa]' in out
    assert '[~/.colusa]' in out
    assert '[default]' in out
    assert 'proj-site.com' in out
    assert 'github.com' in out
