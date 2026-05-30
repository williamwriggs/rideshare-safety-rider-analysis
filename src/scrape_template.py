"""Template for compliant public-data collection.

This file is intentionally a template, not a live scraper. Before collecting data,
confirm that the source allows collection through its API or terms of service, and
consider privacy, human-subjects, and IRB requirements.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd
from textblob import TextBlob


KEYWORDS = ["Waymo", "Uber", "ride", "safety", "comfort", "trust", "pickup", "dropoff"]


@dataclass
class PublicNarrative:
    source: str
    service: str
    text: str
    location: str | None = None
    created_at: str | None = None


def classify_sentiment(text: str) -> tuple[str, float]:
    score = TextBlob(text).sentiment.polarity
    if score > 0.1:
        label = "Positive"
    elif score < -0.1:
        label = "Negative"
    else:
        label = "Neutral"
    return label, score


def tag_scenario(text: str) -> str:
    lower = text.lower()
    if any(term in lower for term in ["pickup", "dropoff", "address", "curb"]):
        return "Pickup/Dropoff"
    if any(term in lower for term in ["unsafe", "scary", "panic", "fear", "anxious"]):
        return "Distress/Comfort"
    if any(term in lower for term in ["smooth", "comfortable", "easy", "reliable"]):
        return "General Experience"
    return "General"


def narratives_to_dataframe(records: Iterable[PublicNarrative]) -> pd.DataFrame:
    rows = []
    for record in records:
        sentiment, score = classify_sentiment(record.text)
        rows.append(
            {
                "Source": record.source,
                "Service": record.service,
                "Scenario": tag_scenario(record.text),
                "Text": record.text,
                "Location": record.location,
                "Created_At": record.created_at,
                "Sentiment": sentiment,
                "Sentiment Score": score,
            }
        )
    return pd.DataFrame(rows)


if __name__ == "__main__":
    demo_records = [
        PublicNarrative(
            source="manual_demo",
            service="Waymo",
            text="The ride felt smooth and easy, but the pickup location was confusing.",
            location="SOMA",
        ),
        PublicNarrative(
            source="manual_demo",
            service="Uber",
            text="The driver helped clarify the dropoff location and the trip felt reliable.",
            location="Mission District",
        ),
    ]
    print(narratives_to_dataframe(demo_records))
