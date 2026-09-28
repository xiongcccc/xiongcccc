#!/usr/bin/env python3
"""Refresh the latest blog posts shown in the profile README."""

from __future__ import annotations

import html
import os
import re
import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin


BLOG_URL = "https://xiongcc.cn/"
START_MARKER = "<!-- BLOG-POST-LIST:START -->"
END_MARKER = "<!-- BLOG-POST-LIST:END -->"
POST_PATTERN = re.compile(
    r'<a\s+class="abstract-title"\s+href="([^"]+)">\s*'
    r'<span\s+class="abstract-title-text">(.*?)</span>.*?'
    r'<time>(\d{4}/\d{2}/\d{2})</time>',
    re.DOTALL,
)


class BlogHomepageParser(HTMLParser):
    """Extract posts from the current ``article.article-row`` layout."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.posts: list[tuple[str, str, str]] = []
        self._article_depth = 0
        self._in_heading = False
        self._capture_title = False
        self._capture_date = False
        self._href = ""
        self._title_parts: list[str] = []
        self._date_parts: list[str] = []
        self._date = ""

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        attributes = dict(attrs)
        classes = set((attributes.get("class") or "").split())

        if tag == "article" and "article-row" in classes:
            self._article_depth = 1
            self._href = ""
            self._title_parts = []
            self._date_parts = []
            self._date = ""
            return

        if not self._article_depth:
            return

        if tag == "article":
            self._article_depth += 1
        elif tag == "h3":
            self._in_heading = True
        elif tag == "a" and self._in_heading and not self._href:
            self._href = attributes.get("href") or ""
            self._capture_title = bool(self._href)
        elif tag == "time":
            self._date = attributes.get("datetime") or ""
            self._capture_date = True

    def handle_data(self, data: str) -> None:
        if self._capture_title:
            self._title_parts.append(data)
        if self._capture_date:
            self._date_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if not self._article_depth:
            return

        if tag == "a" and self._capture_title:
            self._capture_title = False
        elif tag == "time":
            self._capture_date = False
        elif tag == "h3":
            self._in_heading = False
        elif tag == "article":
            self._article_depth -= 1
            if self._article_depth == 0:
                title = " ".join("".join(self._title_parts).split())
                date = self._date or "".join(self._date_parts).strip()
                if self._href and title and date:
                    self.posts.append((self._href, title, date))


def normalize_date(value: str) -> str:
    match = re.search(r"(\d{4})[-./](\d{1,2})[-./](\d{1,2})", value)
    if not match:
        return value.strip()
    year, month, day = (int(part) for part in match.groups())
    return f"{year:04d}-{month:02d}-{day:02d}"


def fetch_homepage() -> str:
    fixture = os.environ.get("BLOG_HTML_FILE")
    if fixture:
        return Path(fixture).read_text(encoding="utf-8")

    request = urllib.request.Request(
        BLOG_URL,
        headers={"User-Agent": "xiongcccc-profile-readme/1.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def latest_posts(page: str, limit: int = 5) -> list[str]:
    posts: list[str] = []
    seen: set[str] = set()

    parser = BlogHomepageParser()
    parser.feed(page)
    parsed_posts = parser.posts

    # Keep compatibility with the previous homepage layout during deployments
    # or rollbacks where the old markup may briefly be served.
    if not parsed_posts:
        parsed_posts = [
            (href, html.unescape(re.sub(r"<[^>]+>", "", raw_title)).strip(), raw_date)
            for href, raw_title, raw_date in POST_PATTERN.findall(page)
        ]

    for href, title, raw_date in parsed_posts:
        url = urljoin(BLOG_URL, html.unescape(href))
        if url in seen:
            continue
        seen.add(url)
        posts.append(f"- {normalize_date(raw_date)} · [{title}]({url})")
        if len(posts) == limit:
            break

    return posts


def update_readme(readme_path: Path, posts: list[str]) -> bool:
    current = readme_path.read_text(encoding="utf-8")
    replacement = f"{START_MARKER}\n" + "\n".join(posts) + f"\n{END_MARKER}"
    updated, count = re.subn(
        rf"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}",
        replacement,
        current,
        count=1,
        flags=re.DOTALL,
    )
    if count != 1:
        raise RuntimeError("README blog post markers are missing or duplicated")
    if updated == current:
        return False
    readme_path.write_text(updated, encoding="utf-8")
    return True


def main() -> int:
    posts = latest_posts(fetch_homepage())
    if not posts:
        print("No blog posts found; keeping the existing README unchanged.", file=sys.stderr)
        return 1

    changed = update_readme(Path("README.md"), posts)
    print(f"Found {len(posts)} posts; README {'updated' if changed else 'already current'}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
