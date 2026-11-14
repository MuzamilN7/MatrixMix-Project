"""Mood search orchestrator: try the AI parser first, fall back to keywords.

    from src.mood_search import search_mood
    result = search_mood(catalog, "something for a rainy Sunday drive")
    result.recs, result.moods, result.source   # source is "ai" or "keywords"
"""
from dataclasses import dataclass, field

import pandas as pd

from src.llm_mood import llm_available, profile_from_text
from src.mood import build_target, parse_mood, rank_by_target


@dataclass
class MoodResult:
    moods: list
    recs: pd.DataFrame
    source: str                    # "ai" or "keywords"
    note: str | None = None        # shown to the user when something unusual happened
    profile: dict = field(default_factory=dict)  # the target audio features that were used


def search_mood(cat: pd.DataFrame, text: str, k: int = 10, clean_only: bool = True,
                use_ai: bool = True, client=None) -> MoodResult:
    """Find songs for a mood request.

    1. If AI is enabled and available, ask the LLM for a profile and rank with it.
    2. If the AI is off, unavailable, fails, or says the text is not a music request,
       use keyword matching instead.
    """
    note = None
    if use_ai and (client is not None or llm_available()):
        profile = profile_from_text(text, client=client)
        if profile is None:
            note = "The AI parser was unavailable, so I used keyword matching instead."
        elif profile.is_music_request:
            recs = rank_by_target(cat, profile.target, profile.genres, k, clean_only)
            return MoodResult([profile.label], recs, "ai", None, profile.target)
        # profile says "not a music request": fall through to keywords, which may still find a mood

    moods = parse_mood(text)
    if not moods:
        return MoodResult([], cat.iloc[0:0], "keywords", note)
    target, hints = build_target(moods)
    return MoodResult(moods, rank_by_target(cat, target, hints, k, clean_only), "keywords", note, target)
