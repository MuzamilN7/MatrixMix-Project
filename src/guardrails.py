"""Guardrails for MatrixMix: input validation, output self-checks, and confidence warnings.

- clean_query():   validates and sanitizes what the user typed (runs BEFORE any search).
- verify_results(): self-check that a recommendation list obeys the system's own rules (runs AFTER ranking).
- confidence():    flags results whose match quality is weak, so the UI can say so instead of sounding sure.
- The "clean only" explicit filter lives in the recommenders (clean_only=True) and is on by default in the app.
"""
import re
from dataclasses import dataclass, field

import pandas as pd

MAX_QUERY_LEN = 100
MAX_PER_ARTIST = 2

# A song-mode list is "low confidence" when its average score is below this.
LOW_CONFIDENCE_SONG = 0.45
# A mood list is "low confidence" when even its best song scores below this.
LOW_CONFIDENCE_MOOD = 0.75


@dataclass
class QueryCheck:
    text: str                      # the cleaned text to actually use
    error: str | None = None       # set when the input can't be used at all
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.error is None


def clean_query(raw) -> QueryCheck:
    """Validate and sanitize user input.

    - non-text or empty input -> error
    - control characters are removed and whitespace is collapsed
    - input with no letters or digits (e.g. "!!!") -> error
    - input longer than MAX_QUERY_LEN is truncated, with a warning
    """
    if not isinstance(raw, str):
        return QueryCheck("", error="Please type some text.")
    text = re.sub(r"[\x00-\x1f\x7f]", " ", raw)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return QueryCheck("", error="Please type something to search for.")
    if not re.search(r"[A-Za-z0-9À-ɏ]", text):
        return QueryCheck("", error="Please use letters or numbers in your search.")
    warnings = []
    if len(text) > MAX_QUERY_LEN:
        text = text[:MAX_QUERY_LEN].rstrip()
        warnings.append(f"Your text was longer than {MAX_QUERY_LEN} characters, so I shortened it.")
    return QueryCheck(text, warnings=warnings)


def _base_title(title: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", re.split(r" \(| - ", str(title).lower())[0]).strip()


def verify_results(recs: pd.DataFrame, k: int = 10, seed_title: str | None = None,
                   max_per_artist: int = MAX_PER_ARTIST) -> list[str]:
    """Self-check a recommendation list. Returns a list of problems (empty list = all rules hold)."""
    problems = []
    if len(recs) > k:
        problems.append(f"returned {len(recs)} songs but k={k}")
    if recs.empty:
        return problems
    if recs.duplicated(subset=["title", "artist"]).any():
        problems.append("contains the same song twice")
    if recs["artist"].str.lower().value_counts().max() > max_per_artist:
        problems.append(f"more than {max_per_artist} songs by one artist")
    if not recs["score"].between(0, 1).all():
        problems.append("a score is outside 0-1")
    if list(recs["score"]) != sorted(recs["score"], reverse=True):
        problems.append("results are not sorted best-first")
    if not recs["why"].map(lambda w: isinstance(w, str) and bool(w.strip())).all():
        problems.append("a result has no explanation")
    if seed_title is not None and (recs["title"].map(_base_title) == _base_title(seed_title)).any():
        problems.append("recommends a version of the song you searched for")
    return problems


def confidence(recs: pd.DataFrame, mode: str) -> str | None:
    """Return a warning message if the results look like weak matches, else None.

    mode is "song" (judged by the average score) or "mood" (judged by the best score).
    """
    if recs.empty:
        return "I couldn't find any songs for that."
    if mode == "song" and recs["score"].mean() < LOW_CONFIDENCE_SONG:
        return ("Low confidence: this song has little genre or era information, "
                "so these matches are rough guesses.")
    if mode == "mood" and recs["score"].max() < LOW_CONFIDENCE_MOOD:
        return "Low confidence: no song fit that mood closely, so these are the nearest options."
    return None
