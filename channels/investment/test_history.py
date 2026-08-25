import os
import tempfile
import unittest
from datetime import date
from pathlib import Path

from history import filter_seen_articles, load_history, save_sent_articles


class InvestmentHistoryTests(unittest.TestCase):
    def test_filters_same_story_by_normalized_url_and_similar_title(self):
        history = [{
            "date": "2026-08-24",
            "title": "直击美团业绩会：Q1亏损环比收窄 - 财联社",
            "url": "https://example.com/meituan?utm_source=rss",
            "companies": ["美团"],
        }]
        articles = [
            {
                "title": "直击美团业绩会：Q1亏损环比收窄 - 另一媒体",
                "url": "https://example.com/another-copy",
                "platform": "Portfolio",
                "portfolio_matches": ["美团"],
            },
            {
                "title": "美团发布新的即时零售产品",
                "url": "https://example.com/new",
                "platform": "Portfolio",
                "portfolio_matches": ["美团"],
            },
        ]
        kept = filter_seen_articles(
            articles, history, similarity_threshold=0.5,
            company_cooldown_days=3, today=date(2026, 8, 25),
        )
        self.assertEqual([item["title"] for item in kept], ["美团发布新的即时零售产品"])
        self.assertGreater(kept[0]["history_penalty"], 1)

    def test_save_and_reload_sent_history(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            previous = os.environ.get("INVESTMENT_HISTORY_PATH")
            os.environ["INVESTMENT_HISTORY_PATH"] = str(Path(temp_dir) / "history.json")
            try:
                article = {
                    "title": "英伟达发布新芯片",
                    "url": "https://example.com/nvda",
                    "platform": "Portfolio",
                    "portfolio_matches": ["英伟达"],
                }
                save_sent_articles([article], [], 30, today=date(2026, 8, 24))
                saved = load_history(30, today=date(2026, 8, 24))
            finally:
                if previous is None:
                    os.environ.pop("INVESTMENT_HISTORY_PATH", None)
                else:
                    os.environ["INVESTMENT_HISTORY_PATH"] = previous
        self.assertEqual(saved[0]["companies"], ["英伟达"])


if __name__ == "__main__":
    unittest.main()
