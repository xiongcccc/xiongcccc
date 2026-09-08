#!/usr/bin/env python3
"""Refresh the latest blog posts shown in the profile README."""

from __future__ import annotations

import html
import os
import re
import sys
import urllib.request
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


def latest_posts(page: str, limit: int = 3) -> list[str]:
    posts: list[str] = []
    seen: set[str] = set()

    for href, raw_title, raw_date in POST_PATTERN.findall(page):
        title = html.unescape(re.sub(r"<[^>]+>", "", raw_title)).strip()
        url = urljoin(BLOG_URL, html.unescape(href))
        if url in seen:
            continue
        seen.add(url)
        posts.append(f"- {raw_date.replace('/', '-')} · [{title}]({url})")
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
