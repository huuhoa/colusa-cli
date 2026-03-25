# -*- coding: utf-8 -*-
"""API for traversing the document nodes."""

import sys
from typing import Any, Callable, Optional

from bs4 import PageElement, NavigableString, Tag, BeautifulSoup


def _warn(msg: Any, *args: Any) -> None:
    print(f'[WARN] {msg}', *args, file=sys.stderr)


def _error(msg: Any, *args: Any) -> None:
    print(f'[ERROR] {msg}', *args, file=sys.stderr)


class NodeVisitor:
    """Walks the abstract syntax tree and calls visitor functions for every node found."""

    def get_visitor(self, node: PageElement) -> Optional[Callable[..., str]]:
        if type(node) is NavigableString:
            method = 'visit_text'
        elif isinstance(node, NavigableString):
            # Comment, CData, Doctype, etc. — non-content NavigableString subclasses
            return lambda *a, **kw: ''
        elif type(node) is Tag:
            method = f'visit_tag_{node.name}'
        elif type(node) is BeautifulSoup:
            method = 'visit_BeautifulSoup'
        else:
            method = 'visit_unknown'
        value = getattr(self, method, None)
        if value is None:
            _warn('Cannot get visit method:', method)
        return value

    def visit(self, node: PageElement, *args: Any, **kwargs: Any) -> str:
        f = self.get_visitor(node)
        if f is not None:
            return f(node, *args, **kwargs)
        return self.generic_visit(node, *args, **kwargs)

    def visit_text(self, node: NavigableString, *args: Any, **kwargs: Any) -> str:
        return node.string or ''

    def visit_unknown(self, node: PageElement, *args: Any, **kwargs: Any) -> str:
        _warn('UNKNOWN Node Type:', node.__class__.__name__)
        return ''

    def visit_BeautifulSoup(self, node: BeautifulSoup, *args: Any, **kwargs: Any) -> str:
        return self.generic_visit(node, *args, **kwargs)

    def generic_visit(self, node: Optional[PageElement], *args: Any, **kwargs: Any) -> str:
        if node is None:
            return ''

        content: list[str] = []
        try:
            for child in node.contents:
                value = self.visit(child, *args, **kwargs)
                content.append(value)
        except TypeError as e:
            _error(e)
        return ''.join(content)
