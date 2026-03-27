"""
Smoke tests for every rule in defaults.toml.

For each rule with a content selector:
  - Build minimal HTML containing exactly one element matching the selector
  - Run DynamicExtractor against it
  - Assert quality == 'full-article' (selector found something)
  - If cleanup selectors are defined, assert they don't raise
"""
import re
import tomllib
from importlib.resources import files

import pytest
from bs4 import BeautifulSoup

from colusa_cli.etr import DynamicExtractor, SiteRule


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_default_rules() -> dict[str, dict]:
    data = files('colusa_cli').joinpath('defaults.toml').read_bytes()
    return tomllib.loads(data.decode()).get('sites', {})


def _element_for_simple_selector(simple: str) -> tuple[str, str]:
    """Parse a simple selector (no combinators) into (tag, attr_string)."""
    tag_match = re.match(r'^([a-zA-Z][a-zA-Z0-9]*)', simple)
    tag = tag_match.group(1) if tag_match else 'div'
    classes = re.findall(r'\.([a-zA-Z_][a-zA-Z0-9_-]*)', simple)
    id_match = re.search(r'#([a-zA-Z_][a-zA-Z0-9_-]*)', simple)
    attrs = re.findall(r'\[([a-zA-Z_][a-zA-Z0-9_-]*)=[\'"]?([^\'"\]]*)[\'"]?\]', simple)
    attr_str = ''
    if classes:
        attr_str += f' class="{" ".join(classes)}"'
    if id_match:
        attr_str += f' id="{id_match.group(1)}"'
    for name, val in attrs:
        attr_str += f' {name}="{val}"'
    return tag, attr_str


def _html_for_selector(selector: str) -> str:
    """Build minimal HTML containing an element that matches the CSS selector.

    Handles: tag, .class, #id, tag.class, tag#id, [attr=val], [attr='val'],
    descendant combinators (space-separated, e.g. '.content main'),
    compound selectors (tag.class[attr=val]), and comma-separated lists
    (uses the first alternative).
    """
    # Use first alternative in comma-separated list
    first = selector.split(',')[0].strip()

    # Split on descendant combinator (spaces not inside brackets)
    parts = re.split(r'\s+(?![^\[]*\])', first)

    # Build nested HTML from outermost to innermost
    inner = '<p>Article content.</p>'
    for part in reversed(parts):
        tag, attr_str = _element_for_simple_selector(part)
        inner = f'<{tag}{attr_str}>{inner}</{tag}>'

    return f'<html><body>{inner}</body></html>'


def _rule_params():
    """Yield (pattern, SiteRule) for all rules that have a content selector."""
    rules = _load_default_rules()
    return [
        pytest.param(pattern, SiteRule(**{k: v for k, v in table.items()}), id=pattern)
        for pattern, table in rules.items()
        if table.get('content')
    ]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('pattern,rule', _rule_params())
def test_content_selector_finds_element(pattern: str, rule: SiteRule) -> None:
    """DynamicExtractor must reach quality='full-article' on synthetic HTML."""
    html = _html_for_selector(rule.content)
    bs = BeautifulSoup(html, 'html.parser')
    extractor = DynamicExtractor(bs, rule)
    extractor.parse()
    assert extractor.quality == 'full-article', (
        f'Selector {rule.content!r} for pattern {pattern!r} did not match '
        f'the constructed HTML:\n{html}'
    )


@pytest.mark.parametrize('pattern,rule', _rule_params())
def test_cleanup_selectors_are_valid(pattern: str, rule: SiteRule) -> None:
    """Cleanup selectors must not raise when applied (even if they match nothing)."""
    if not rule.cleanup:
        pytest.skip('no cleanup selectors')
    html = _html_for_selector(rule.content)
    bs = BeautifulSoup(html, 'html.parser')
    extractor = DynamicExtractor(bs, rule)
    extractor.parse()
    # Should not raise even when cleanup selectors match nothing
    extractor.cleanup()
