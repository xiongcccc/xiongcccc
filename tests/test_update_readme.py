import unittest

from scripts.update_readme import latest_posts


class LatestPostsTest(unittest.TestCase):
    def test_current_article_row_layout(self) -> None:
        page = """
        <article class="article-row">
          <time datetime="2026-09-24">2026.09.24</time>
          <div>
            <h3><a href="/2026/09/24/new-post/">New &amp; useful post</a></h3>
          </div>
          <a class="row-arrow" href="/2026/09/24/new-post/">Read</a>
        </article>
        """

        self.assertEqual(
            latest_posts(page),
            [
                "- 2026-09-24 · [New & useful post]"
                "(https://xiongcc.cn/2026/09/24/new-post/)"
            ],
        )

    def test_previous_abstract_title_layout(self) -> None:
        page = """
        <a class="abstract-title" href="/2026/09/07/old-post/">
          <span class="abstract-title-text">Previous post</span>
          <time>2026/09/07</time>
        </a>
        """

        self.assertEqual(
            latest_posts(page),
            [
                "- 2026-09-07 · [Previous post]"
                "(https://xiongcc.cn/2026/09/07/old-post/)"
            ],
        )


if __name__ == "__main__":
    unittest.main()
