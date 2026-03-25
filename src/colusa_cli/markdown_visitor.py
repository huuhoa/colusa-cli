import re
from typing import Any, Callable, Optional

import requests.compat
from bs4 import Tag

from .visitor import NodeVisitor


class MarkdownVisitor(NodeVisitor):

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def text_cleanup(self, text: str) -> str:
        text = text.strip()
        text = re.sub(r'\n\s*', ' ', text)
        return text

    def tag_wrap_around(self, text: str, w: str) -> str:
        if not text:
            return ''
        new_text = text.strip()
        if not new_text:
            return ''
        begin, t, end = text.partition(new_text)
        return f'{begin}{w}{t}{w}{end}'

    def get_image_from_srcset(self, srcset: Optional[str], default_src: str, default_dim: str) -> tuple[str, str]:
        if srcset is None:
            return default_dim, default_src

        srcs = srcset.split(',')
        imgs: dict[str, str] = {}
        for s in srcs:
            parts = s.strip().split()
            if len(parts) >= 2:
                imgs[parts[1].strip()] = parts[0].strip()
        if not imgs:
            return default_dim, default_src

        def _dim_key(x: str) -> float:
            try:
                return float(re.sub(r'[whx]', '', x))
            except ValueError:
                return 0.0

        dim_list = sorted(imgs.keys(), key=_dim_key)
        largest = dim_list[-1]
        src = imgs[largest]
        dim = default_dim
        if 'w' in largest:
            dim = f"{largest.replace('w', '')},"
        if 'h' in largest:
            dim = f",{largest.replace('h', '')}"

        return dim, src

    # ------------------------------------------------------------------ #
    # Fall-through and ignore tags
    # ------------------------------------------------------------------ #

    def visit_tag_fall_through(self, node: Tag, *args: Any, **kwargs: Any) -> str:
        return self.generic_visit(node, *args, **kwargs)

    def visit_tag_ignore_content(self, node: Tag, *args: Any, **kwargs: Any) -> str:
        return ''

    visit_tag_span = visit_tag_fall_through
    visit_tag_section = visit_tag_fall_through
    visit_tag_input = visit_tag_fall_through
    visit_tag_picture = visit_tag_fall_through
    visit_tag_font = visit_tag_fall_through
    visit_tag_center = visit_tag_fall_through
    visit_tag_sup = visit_tag_fall_through
    visit_tag_sub = visit_tag_fall_through
    visit_tag_div = visit_tag_fall_through
    visit_tag_article = visit_tag_fall_through
    visit_tag_header = visit_tag_fall_through
    visit_tag_footer = visit_tag_fall_through
    visit_tag_aside = visit_tag_fall_through
    visit_tag_nav = visit_tag_fall_through
    visit_tag_main = visit_tag_fall_through
    visit_tag_label = visit_tag_fall_through
    visit_tag_abbr = visit_tag_fall_through
    visit_tag_cite = visit_tag_fall_through
    visit_tag_time = visit_tag_fall_through
    visit_tag_mark = visit_tag_fall_through
    visit_tag_small = visit_tag_fall_through
    visit_tag_details = visit_tag_fall_through
    visit_tag_summary = visit_tag_fall_through
    visit_tag_dd = visit_tag_fall_through
    visit_tag_dt = visit_tag_fall_through
    visit_tag_dl = visit_tag_fall_through

    visit_tag_iframe = visit_tag_ignore_content
    visit_tag_style = visit_tag_ignore_content
    visit_tag_svg = visit_tag_ignore_content
    visit_Stylesheet = visit_tag_ignore_content
    visit_Comment = visit_tag_ignore_content
    visit_tag_button = visit_tag_ignore_content
    visit_tag_form = visit_tag_ignore_content
    visit_tag_script = visit_tag_ignore_content
    visit_tag_link = visit_tag_ignore_content     # <link> HTML element (not <a>)
    visit_tag_meta = visit_tag_ignore_content
    visit_tag_noscript = visit_tag_ignore_content
    visit_tag_source = visit_tag_ignore_content   # <source> inside <picture>/<video>

    # ------------------------------------------------------------------ #
    # Headings
    # ------------------------------------------------------------------ #

    def _visit_heading_node(level: int) -> Callable[['MarkdownVisitor', Tag, Any, Any], str]:  # type: ignore[misc]
        def visitor(self: 'MarkdownVisitor', node: Tag, *args: Any, **kwargs: Any) -> str:
            text = self.text_cleanup(self.generic_visit(node, *args, **kwargs))
            if not text:
                return '\n\n'
            return f'\n{"#" * level} {text}\n\n'
        return visitor

    visit_tag_h1 = _visit_heading_node(1)
    visit_tag_h2 = _visit_heading_node(2)
    visit_tag_h3 = _visit_heading_node(3)
    visit_tag_h4 = _visit_heading_node(4)
    visit_tag_h5 = _visit_heading_node(5)
    visit_tag_h6 = _visit_heading_node(6)

    # ------------------------------------------------------------------ #
    # Inline formatting
    # ------------------------------------------------------------------ #

    def visit_tag_strong(self, node: Tag, *args: Any, **kwargs: Any) -> str:
        text = self.generic_visit(node, *args, **kwargs)
        return self.tag_wrap_around(text, '**')

    visit_tag_b = visit_tag_strong

    def visit_tag_em(self, node: Tag, *args: Any, **kwargs: Any) -> str:
        text = self.generic_visit(node, *args, **kwargs)
        return self.tag_wrap_around(text, '*')

    visit_tag_i = visit_tag_em
    visit_tag_u = visit_tag_em

    def visit_tag_q(self, node: Tag, *args: Any, **kwargs: Any) -> str:
        text = self.generic_visit(node, *args, **kwargs)
        return f'"{text}"'

    def visit_tag_del(self, node: Tag, *args: Any, **kwargs: Any) -> str:
        text = self.generic_visit(node, *args, **kwargs)
        return self.tag_wrap_around(text, '~~')

    visit_tag_s = visit_tag_del

    # ------------------------------------------------------------------ #
    # Block elements
    # ------------------------------------------------------------------ #

    def visit_tag_p(self, node: Tag, *args: Any, **kwargs: Any) -> str:
        text = self.generic_visit(node, *args, **kwargs)
        return f'{text.strip()}\n\n'

    def visit_tag_hr(self, node: Tag, *args: Any, **kwargs: Any) -> str:
        return '\n---\n\n'

    def visit_tag_br(self, node: Tag, *args: Any, **kwargs: Any) -> str:
        pre = kwargs.get('pre')
        text = self.generic_visit(node, *args, **kwargs) if node.contents else ''
        if not pre:
            return f'\n\n{text}'
        return f'\n{text}'

    def visit_tag_blockquote(self, node: Tag, *args: Any, **kwargs: Any) -> str:
        cite_node = node.find('cite')
        cite: Optional[str] = None
        if cite_node is not None:
            cite_node.extract()
            cite = cite_node.get_text(strip=True)
        text = self.generic_visit(node, *args, **kwargs).strip()
        lines = text.split('\n')
        quoted = '\n'.join(f'> {line}' if line.strip() else '>' for line in lines)
        if cite:
            quoted += f'\n>\n> — {cite}'
        return f'{quoted}\n\n'

    # ------------------------------------------------------------------ #
    # Links and images
    # ------------------------------------------------------------------ #

    def visit_tag_a(self, node: Tag, *args: Any, **kwargs: Any) -> str:
        href = node.get('href', '')
        text = self.generic_visit(node, *args, **kwargs)
        if not text:
            return ''
        if not re.match(r'https?://', href):
            return text
        # anchor wrapping a single image — let the image tag handle it
        if len(node.contents) == 1:
            child = node.contents[0]
            if isinstance(child, Tag) and child.name == 'img':
                return text
        return f'[{text}]({href})'

    def visit_tag_img(self, node: Tag, *args: Any, **kwargs: Any) -> str:
        src = node.get('src') or node.get('data-src', '')
        if not src:
            return ''
        srcset = node.get('srcset') or node.get('data-srcset')
        _, src = self.get_image_from_srcset(srcset, src, '')
        src_url = kwargs.get('src_url', '')
        url = requests.compat.urljoin(src_url, src)
        if not url.startswith(('http://', 'https://')):
            return ''
        alt = node.get('alt', '')
        caption = kwargs.get('caption')
        if caption:
            return f'![{alt}]({url})\n*{caption}*'
        return f'![{alt}]({url})'

    def visit_tag_figure(self, node: Tag, *args: Any, **kwargs: Any) -> str:
        caption_node = node.find('figcaption')
        if caption_node is not None:
            kwargs['caption'] = caption_node.get_text(strip=True)
            caption_node.extract()
        # Medium uses paragraph-image with a noscript containing the real img
        node_to_visit = node
        if 'paragraph-image' in node.get('class', []):
            noscript = node.find('noscript')
            if noscript is not None:
                node_to_visit = noscript
        text = self.generic_visit(node_to_visit, *args, **kwargs)
        if caption_node is not None:
            kwargs.pop('caption', None)
        return f'{text}\n\n'

    # ------------------------------------------------------------------ #
    # Lists
    # ------------------------------------------------------------------ #

    def visit_tag_ul(self, node: Tag, *args: Any, **kwargs: Any) -> str:
        return self._wrapper_list(node, 'ul', *args, **kwargs)

    def visit_tag_ol(self, node: Tag, *args: Any, **kwargs: Any) -> str:
        return self._wrapper_list(node, 'ol', *args, **kwargs)

    def _wrapper_list(self, node: Tag, list_type: str, *args: Any, **kwargs: Any) -> str:
        indent: int = kwargs.get('indent', 0) + 1
        indent_stack: list[str] = list(kwargs.get('indent_stack', []))
        indent_stack.append(list_type)
        kwargs['indent'] = indent
        kwargs['indent_stack'] = indent_stack
        text = self.generic_visit(node, *args, **kwargs)
        kwargs['indent'] = indent - 1
        kwargs['indent_stack'] = indent_stack[:-1]
        return f'{text}\n'

    def visit_tag_li(self, node: Tag, *args: Any, **kwargs: Any) -> str:
        text = self.generic_visit(node, *args, **kwargs).strip()
        if not text:
            return ''
        indent: int = kwargs.get('indent', 1)
        indent_stack: list[str] = kwargs.get('indent_stack', [])
        if not indent_stack:
            return ''
        last = indent_stack[-1]
        prefix = '  ' * (indent - 1)
        marker = '-' if last == 'ul' else '1.'
        return f'{prefix}{marker} {text}\n'

    # ------------------------------------------------------------------ #
    # Code
    # ------------------------------------------------------------------ #

    def visit_tag_code(self, node: Tag, *args: Any, **kwargs: Any) -> str:
        text = self.generic_visit(node, *args, **kwargs)
        if '\n' in text or kwargs.get('pre'):
            lang_list = node.get('class', ['text'])
            lang = lang_list[0] if lang_list else 'text'
            lang = lang.replace('language-', '')
            return f'```{lang}\n{text}\n```\n'
        return f'`{text}`'

    def visit_tag_pre(self, node: Tag, *args: Any, **kwargs: Any) -> str:
        kwargs['pre'] = True
        text = self.generic_visit(node, *args, **kwargs)
        kwargs.pop('pre', None)
        # If a code child already rendered a fenced block, return as-is
        if text.startswith('```'):
            return f'{text}\n'
        return f'```\n{text}\n```\n\n'

    # ------------------------------------------------------------------ #
    # Tables
    # ------------------------------------------------------------------ #

    def visit_tag_table(self, node: Tag, *args: Any, **kwargs: Any) -> str:
        all_tr = node.find_all('tr')
        rows: list[list[str]] = []
        headers: list[str] = []

        for tr in all_tr:
            cells: list[str] = []
            for td in tr.contents:
                if not isinstance(td, Tag):
                    continue
                if td.name == 'th':
                    headers.append(self.generic_visit(td, *args, **kwargs).strip())
                elif td.name == 'td':
                    cells.append(self.generic_visit(td, *args, **kwargs).strip())
            if cells:
                rows.append(cells)

        if not headers and not rows:
            return ''

        num_cols = max(
            len(headers),
            max((len(r) for r in rows), default=0),
        )

        def fmt_row(cells: list[str]) -> str:
            padded = cells + [''] * (num_cols - len(cells))
            return '| ' + ' | '.join(padded) + ' |'

        lines: list[str] = []
        if headers:
            lines.append(fmt_row(headers))
        else:
            # GFM requires a header row
            lines.append(fmt_row([''] * num_cols))

        lines.append('| ' + ' | '.join(['---'] * num_cols) + ' |')

        for row in rows:
            lines.append(fmt_row(row))

        return '\n'.join(lines) + '\n\n'
