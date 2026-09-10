import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from ideas import load_idea_history, record_content_ideas, select_content_ideas


NOW = datetime(2026, 8, 24, 8, tzinfo=timezone.utc)


def article(topic: str, url: str, *, platform: str = "News") -> dict:
    return {
        "title": f"{topic} latest event",
        "title_zh": f"{topic}最新事件",
        "source": "Primary Source",
        "url": url,
        "platform": platform,
        "priority": 3,
        "score": 8,
        "published_at": "2026-08-24T06:00:00+00:00",
        "idea_topic_zh": topic,
        "news_hook_zh": "今天披露一个新的关键数字",
        "investment_angle_zh": "事实→传导链→潜在受益者（推论）",
    }


class ContentIdeaTests(unittest.TestCase):
    def test_memory_aliases_share_one_cooldown(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "history.jsonl"
            old = article("存储芯片", "https://old")
            record_content_ideas([old], path, datetime(2026, 8, 20, tzinfo=timezone.utc))
            selected = select_content_ideas(
                [article("HBM供需", "https://new"), article("在线旅游", "https://travel")],
                path,
                now=NOW,
            )
            self.assertEqual([item["idea_topic_zh"] for item in selected], ["在线旅游"])

    def test_same_day_rerun_is_sticky(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "history.jsonl"
            chosen = article("AI模型", "https://same")
            record_content_ideas([chosen], path, NOW)
            selected = select_content_ideas([chosen], path, now=NOW)
            self.assertEqual([item["url"] for item in selected], ["https://same"])

    def test_old_insight_is_not_a_today_hook(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate = article("金融科技", "https://old", platform="Memo")
            candidate["published_at"] = "2026-08-10T06:00:00+00:00"
            selected = select_content_ideas([candidate], Path(tmp) / "history.jsonl", now=NOW)
            self.assertEqual(selected, [])

    def test_history_uses_beijing_digest_date(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "history.jsonl"
            record_content_ideas(
                [article("在线旅游", "https://travel")],
                path,
                datetime(2026, 8, 24, 23, 30, tzinfo=timezone.utc),
            )
            self.assertEqual(load_idea_history(path)[0]["date"], "2026-08-25")


if __name__ == "__main__":
    unittest.main()
