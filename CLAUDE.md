# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Using colusa-cli as a tool

When you need to read a web page, use `colusa-cli` to fetch and convert it to Markdown.

```bash
SSL_CERT_FILE=/opt/homebrew/etc/openssl@3/cert.pem .venv/bin/colusa-cli <url>
```

### Output format

The tool prints to stdout:

```
---
title: "Article Title"
source: "https://..."
author: "Name"          # omitted if not found
published: "2024-03-01" # omitted if not found
quality: full-article   # or: body-fallback
---

# Article Title

...markdown body...
```

### Interpreting `quality`

- `full-article` — main article content was isolated; output is clean
- `body-fallback` — no article element found; output is the full page body and may include navigation, sidebars, and boilerplate

### When extraction fails

- **Exit 0** — success (includes `body-fallback` case)
- **Exit 1** — hard failure (network error, page has no `<body>`); nothing useful on stdout

### Flags

- `--selector "CSS"` — override auto-detection with a CSS selector when `quality: body-fallback` and you can identify the right element
- `--no-cache` — force re-fetch (cache lives at `~/.cache/colusa-cli/`)

---

## Development commands

```bash
# Setup
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"

# Tests
.venv/bin/pytest
```

## Architecture

```
cli.py → Downloader.fetch(url) → BeautifulSoup → Extractor → MarkdownVisitor → stdout
```

- **`fetch.py`** — HTTP download with `~/.cache/colusa-cli/<sha256>` disk cache; uses `ssl.get_default_verify_paths()` for macOS SSL
- **`etr.py`** — `Extractor` isolates article body (hentry → known CSS classes → `<article>` → `<main>` → `<body>` fallback); extracts title/author/published from OpenGraph + Yoast JSON-LD; `DynamicExtractor` accepts a CSS selector override
- **`markdown_visitor.py`** — `MarkdownVisitor` walks the BeautifulSoup tree via the visitor pattern, one `visit_tag_*()` method per HTML tag
- **`visitor.py`** — `NodeVisitor` base class (adapted from colusa); dispatches to `visit_tag_<name>()` recursively

Core logic adapted from `../colusa`. Do not port back: AsciiDoc output, `Render`, `Crawler`, `Colusa` orchestrator, plugin system, Tor support, image downloading.
