"""
Headless browser fetcher using Playwright.
Used for sites with bot detection (Medium, etc.) that block plain requests.
"""

import sys


def fetch(url: str) -> str:
    """Fetch a URL using a headless Chromium browser and return the page HTML."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(
            '[ERROR] playwright is required for --browser. '
            'Install with: pip install "colusa-cli[browser]" '
            'then run: playwright install chromium',
            file=sys.stderr,
        )
        raise SystemExit(1)

    print('[browser] Launching headless Chromium...', file=sys.stderr)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
            viewport={'width': 1280, 'height': 800},
            locale='en-US',
        )
        page = context.new_page()
        page.goto(url, wait_until='domcontentloaded', timeout=30_000)
        # Wait a bit for JS-rendered content to settle
        page.wait_for_timeout(2_000)
        html = page.content()
        browser.close()

    print('[browser] Done.', file=sys.stderr)
    return html
