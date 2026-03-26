import json
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from bs4 import Tag, BeautifulSoup
from dateutil import parser as dateutil_parser


@dataclass
class SiteRule:
    content: str = ''
    title: str = ''
    author: str = ''
    published: str = ''
    cleanup: list[str] = field(default_factory=list)
    browser: bool = False


class ContentNotFoundError(Exception):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def __str__(self) -> str:
        return 'cannot detect content of the site'


class Extractor:
    """Extracts the main article content from a BeautifulSoup-parsed page."""

    def __init__(self, bs: BeautifulSoup) -> None:
        self.bs: BeautifulSoup = bs
        self.url_path: Optional[str] = None
        self.content: Optional[Tag] = None
        self.author: Optional[str] = None
        self.published: Optional[str] = None
        self.title: Optional[str] = None
        self.extra_metadata: str = ''
        self.main_content: Optional[Tag] = None
        self.quality: str = 'full-article'

    def parse(self) -> None:
        self.main_content = self._find_main_content()
        if self.main_content is None:
            # Fall back to <body> rather than hard-failing
            self.main_content = self.bs.find('body')
            self.quality = 'body-fallback'
        else:
            self.quality = 'full-article'
        if self.main_content is None:
            raise ContentNotFoundError()
        self._parse_metadata()

    def _parse_title(self) -> str:
        meta = self.bs.find('meta', attrs={'property': 'og:title'})
        if meta is not None:
            return meta.get('content', '')
        title_tag = self.bs.find('title')
        return title_tag.text if title_tag else ''

    def _parse_published(self) -> str:
        meta = self.bs.find('meta', attrs={'property': 'article:published_time'})
        value = meta.get('content') if meta else None
        if value is not None:
            published = dateutil_parser.parse(value)
            return str(published.date())

        time_published = self.bs.find('time', attrs={'class': 'entry-date published'})
        if time_published is not None:
            return time_published.text

        return ''

    def _parse_author(self) -> str:
        meta = self.bs.find('meta', attrs={'name': 'author'})
        if meta is not None:
            value = meta.get('content')
            if value is not None:
                return value
        return ''

    def _parse_extra_metadata(self) -> str:
        return ''

    @classmethod
    def remove_tag(cls, site: Optional[Tag], tag: str, attrs: dict[str, Any]) -> None:
        if site is None:
            return
        elements = site.find_all(tag, attrs=attrs)
        if elements is None:
            return
        for e in elements:
            e.decompose()

    def cleanup(self) -> None:
        self.remove_tag(self.main_content, 'div', attrs={'class': 'site-branding'})
        self.remove_tag(self.main_content, 'div', attrs={'class': 'navigation-top'})
        self.remove_tag(self.main_content, 'footer', attrs={})
        self.remove_tag(self.main_content, 'div', attrs={'class': 'searchsettings'})
        self.remove_tag(self.main_content, 'section', attrs={'id': 'ajaxsearchlitewidget-2'})
        self.remove_tag(self.main_content, 'aside', attrs={'id': 'secondary'})
        self.remove_tag(self.main_content, 'nav', attrs={'class': 'post-navigation'})
        self.remove_tag(self.main_content, 'header', attrs={'id': 'masthead'})

    def get_content(self) -> Optional[Tag]:
        return self.main_content

    def _find_main_content(self) -> Optional[Tag]:
        def is_content_class(css_class: Optional[str]) -> bool:
            return css_class is not None and css_class in [
                'postcontent',
                'entry-content',
                'article-content',
                'blog-content',
            ]

        site = self.bs.find(class_='hentry')
        if site is not None:
            role_main = site.find('div', attrs={'role': 'main'})
            if role_main is not None:
                site = role_main
            role_main = site.find('div', attrs={'class': 'td-post-content'})
            if role_main is not None:
                site = role_main
            return site

        tag = self.bs.find('div', class_=is_content_class)
        if tag is not None:
            return tag

        hs_blog_post = self.bs.find(attrs={'class': 'hs-blog-post'})
        if hs_blog_post is not None:
            blog_content = hs_blog_post.find(attrs={'class': 'post-body'})
            return blog_content

        tag = self.bs.find('article')
        if tag is not None:
            return tag

        tag = self.bs.find('main')
        if tag is not None:
            return tag

        return None

    def _parse_yoast_data(self) -> dict[str, str]:
        yoast_data = self.bs.find('script', attrs={
            'type': 'application/ld+json',
            'class': 'yoast-schema-graph',
        })

        return_data: dict[str, str] = {}
        if yoast_data is None:
            return return_data

        data = json.loads(yoast_data.string)
        graph = data.get('@graph', [])
        persons: dict[str, str] = {}
        author: Optional[str] = None
        for g in graph:
            if type(g) is not dict:
                continue
            g_type = g.get('@type', '')
            if g_type == 'Article':
                author = g.get('author', {}).get('@id')
                published_value = g.get('datePublished')
                if published_value:
                    published = dateutil_parser.parse(published_value)
                    return_data['published'] = str(published.date())
                headline = g.get('headline')
                if headline:
                    return_data['title'] = headline

            if (type(g_type) is list and 'Person' in g_type) or (type(g_type) is str and g_type == 'Person'):
                person_id = g.get('@id', '')
                person_name = g.get('name', '')
                persons[person_id] = person_name

        if author in persons:
            return_data['author'] = persons[author]

        return return_data

    def _parse_metadata(self) -> None:
        self.title = self._parse_title()
        self.author = self._parse_author()
        self.published = self._parse_published()
        self.extra_metadata = self._parse_extra_metadata()
        data = self._parse_yoast_data()
        self.title = data.get('title', self.title)
        self.author = data.get('author', self.author)
        self.published = data.get('published', self.published)


class DynamicExtractor(Extractor):
    """Extractor driven by user-supplied CSS selectors from a SiteRule."""

    def __init__(self, bs: BeautifulSoup, rule: SiteRule) -> None:
        super().__init__(bs)
        self._rule = rule

    def _find_main_content(self) -> Optional[Tag]:
        if self._rule.content:
            tag = self.bs.select_one(self._rule.content)
            if tag is not None:
                return tag
        return super()._find_main_content()

    def _parse_title(self) -> str:
        if self._rule.title:
            tag = self.bs.select_one(self._rule.title)
            if tag is not None:
                return tag.get_text(strip=True)
        return super()._parse_title()

    def _parse_author(self) -> str:
        if self._rule.author:
            tag = self.bs.select_one(self._rule.author)
            if tag is not None:
                return tag.get_text(strip=True)
        return super()._parse_author()

    def _parse_published(self) -> str:
        if self._rule.published:
            tag = self.bs.select_one(self._rule.published)
            if tag is not None:
                return tag.get_text(strip=True)
        return super()._parse_published()

    def cleanup(self) -> None:
        super().cleanup()
        if self.main_content is None:
            return
        for selector in self._rule.cleanup:
            for el in self.main_content.select(selector):
                el.decompose()
