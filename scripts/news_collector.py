"""
MVP-парсер новостей для раздела "Новости".
Запуск: python scripts/news_collector.py
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

import feedparser

KEYWORDS = [
    "лифт",
    "подъемник",
    "новые правила",
    "ростехнадзор",
    "авария",
    "запчасти",
]

RSS_SOURCES = [
    # Заполним реальными источниками на следующем шаге.
    "https://example.com/rss",
]

OUTPUT_FILE = Path("instance/news_candidates.json")


@dataclass
class NewsItem:
    title: str
    link: str
    summary: str
    source: str
    published: str


def contains_keywords(text: str, keywords: Iterable[str]) -> bool:
    text_lower = (text or "").lower()
    return any(keyword in text_lower for keyword in keywords)


def collect_from_rss() -> list[NewsItem]:
    items: list[NewsItem] = []
    for source in RSS_SOURCES:
        parsed = feedparser.parse(source)
        for entry in parsed.entries:
            title = getattr(entry, "title", "")
            summary = getattr(entry, "summary", "")
            content = f"{title}\n{summary}"
            if not contains_keywords(content, KEYWORDS):
                continue
            items.append(
                NewsItem(
                    title=title.strip(),
                    link=getattr(entry, "link", "").strip(),
                    summary=summary.strip(),
                    source=source,
                    published=getattr(entry, "published", "").strip(),
                )
            )
    return items


def main() -> None:
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    news = collect_from_rss()
    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "count": len(news),
        "items": [asdict(item) for item in news],
    }
    OUTPUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {len(news)} items to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
