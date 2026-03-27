import argparse
import os
import pathlib
import re
import sys

import requests
from bs4 import BeautifulSoup

from .config import ConfigError, load_config, match_site_rule
from .etr import ContentNotFoundError, DynamicExtractor, Extractor, SiteRule
from .fetch import Downloader
from .markdown_visitor import MarkdownVisitor


def _yaml_str(value: str) -> str:
    """Escape a string value for YAML."""
    escaped = value.replace('\\', '\\\\').replace('"', '\\"')
    return f'"{escaped}"'


def _print_rules(sites: list) -> None:
    """Print active site rules as a table: PATTERN, CONTENT, SOURCE."""
    from .etr import SiteRule
    if not sites:
        print('No site rules configured.')
        return
    col_pat = max(len('PATTERN'), max(len(p) for p, _, _ in sites))
    col_con = max(len('CONTENT'), max(len(r.content) for _, r, _ in sites))
    fmt = f'{{:<{col_pat}}}  {{:<{col_con}}}  {{}}'
    print(fmt.format('PATTERN', 'CONTENT', 'SOURCE'))
    print(fmt.format('-' * col_pat, '-' * col_con, '--------'))
    for pattern, rule, source in sites:
        print(fmt.format(pattern, rule.content, source))


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Fetch a URL and output the main article content as Markdown.',
    )
    parser.add_argument('url', nargs='?', help='URL to fetch and convert')
    parser.add_argument(
        '--selector', '-s',
        metavar='CSS',
        help='CSS selector to locate article content (overrides auto-detection)',
    )
    parser.add_argument(
        '--cache-dir',
        type=pathlib.Path,
        metavar='DIR',
        help='Directory for cached HTML (default: ~/.cache/colusa-cli/)',
    )
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Skip disk cache and always re-fetch',
    )
    parser.add_argument(
        '--ssl-cert',
        metavar='FILE',
        help='Path to CA bundle for SSL verification',
    )
    parser.add_argument(
        '--doh',
        nargs='?',
        const='cloudflare',
        metavar='SERVER',
        help='Resolve DNS via DoH to bypass ISP blocks. '
             'SERVER: cloudflare (default), google, quad9, or a full DoH URL.',
    )
    parser.add_argument(
        '--browser',
        action='store_true',
        help='Fetch using a headless Chromium browser (bypasses bot detection).',
    )
    parser.add_argument(
        '--list-rules',
        action='store_true',
        help='Print all active site rules (defaults + ~/.colusa + .colusa) and exit.',
    )
    args = parser.parse_args()

    # Load config
    try:
        config = load_config()
    except ConfigError as exc:
        print(f'[ERROR] {exc}', file=sys.stderr)
        raise SystemExit(1)

    if args.list_rules:
        _print_rules(config.sites)
        raise SystemExit(0)

    if not args.url:
        parser.error('url is required (unless --list-rules is specified)')

    # Resolve scalar settings: CLI flag > config > env var > system default
    ssl_cert: str | None = (
        args.ssl_cert
        or config.ssl_cert
        or os.environ.get('SSL_CERT_FILE')
    )
    cache_dir: pathlib.Path | None = args.cache_dir or config.cache_dir
    doh: str | None = args.doh or config.doh
    use_browser: bool = args.browser or config.browser

    # Match site rule from config
    site_rule: SiteRule | None = match_site_rule(args.url, config.sites)
    if site_rule is not None and site_rule.browser:
        use_browser = True

    if doh:
        from . import doh as doh_mod
        doh_mod.enable(doh)

    # Fetch
    html: str | None = None
    if use_browser:
        from . import browser as browser_mod
        try:
            html = browser_mod.fetch(args.url)
        except SystemExit:
            raise
        except Exception as exc:
            print(f'[ERROR] Browser fetch failed: {exc}', file=sys.stderr)
            raise SystemExit(1)
    else:
        try:
            downloader = Downloader(cache_dir=cache_dir, ssl_cert=ssl_cert)
            html = downloader.fetch(args.url, no_cache=args.no_cache)
        except requests.exceptions.HTTPError as exc:
            if exc.response is not None and exc.response.status_code in (403, 429):
                print(
                    f'[WARN] {exc.response.status_code} from server — '
                    'retrying with headless browser...',
                    file=sys.stderr,
                )
                from . import browser as browser_mod
                try:
                    html = browser_mod.fetch(args.url)
                except SystemExit:
                    raise
                except Exception as browser_exc:
                    print(f'[ERROR] Browser fallback failed: {browser_exc}', file=sys.stderr)
                    raise SystemExit(1)
            else:
                print(f'[ERROR] Failed to fetch {args.url}: {exc}', file=sys.stderr)
                raise SystemExit(1)
        except Exception as exc:
            print(f'[ERROR] Failed to fetch {args.url}: {exc}', file=sys.stderr)
            raise SystemExit(1)

    # Parse
    bs = BeautifulSoup(html, 'html.parser')

    # Extract: CLI --selector overrides config rule's content; config rule fills the rest
    if args.selector:
        rule = SiteRule(content=args.selector)
        extractor: Extractor = DynamicExtractor(bs, rule)
    elif site_rule is not None:
        extractor = DynamicExtractor(bs, site_rule)
    else:
        extractor = Extractor(bs)

    extractor.url_path = args.url

    try:
        extractor.parse()
    except ContentNotFoundError as exc:
        print(f'[ERROR] {exc}', file=sys.stderr)
        raise SystemExit(1)

    extractor.cleanup()
    content = extractor.get_content()

    # Convert to Markdown
    visitor = MarkdownVisitor()
    body = visitor.visit(content, src_url=args.url)
    body = re.sub(r'(\n\s*){3,}', '\n\n', body).strip()

    # YAML frontmatter
    title = extractor.title or ''
    fm: list[str] = ['---']
    if title:
        fm.append(f'title: {_yaml_str(title)}')
    fm.append(f'source: {_yaml_str(args.url)}')
    if extractor.author:
        fm.append(f'author: {_yaml_str(extractor.author)}')
    if extractor.published:
        fm.append(f'published: {_yaml_str(extractor.published)}')
    fm.append(f'quality: {extractor.quality}')
    fm.append('---')

    # Markdown body
    heading = f'# {title}' if title else ''
    parts = ['\n'.join(fm)]
    if heading:
        parts.append(heading)
    parts.append(body)

    print('\n\n'.join(parts))


if __name__ == '__main__':
    main()
