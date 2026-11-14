"""Mood search against the real catalog: does each mood actually return songs that sound right?"""
import pytest

from src.mood import PROFILES, recommend_by_mood
from src.similar import build_catalog


@pytest.fixture(scope="module")
def cat():
    return build_catalog()


@pytest.mark.parametrize("mood", sorted(PROFILES))
def test_every_mood_returns_ten_valid_results(cat, mood):
    moods, recs = recommend_by_mood(cat, mood, k=10)
    assert mood in moods
    assert len(recs) == 10
    assert recs["score"].between(0, 1).all()
    assert recs["artist"].value_counts().max() <= 2
    assert recs["energy"].notna().all()


@pytest.mark.parametrize("mood,feature,check", [
    ("workout",  "energy",       lambda v: v > 0.75),
    ("party",    "danceability", lambda v: v > 0.65),
    ("angry",    "energy",       lambda v: v > 0.75),
    ("sleep",    "energy",       lambda v: v < 0.35),
    ("chill",    "energy",       lambda v: v < 0.5),
    ("cafe",     "acousticness", lambda v: v > 0.4),
    ("happy",    "valence",      lambda v: v > 0.6),
    ("sad",      "valence",      lambda v: v < 0.35),
])
def test_results_actually_match_the_mood(cat, mood, feature, check):
    _, recs = recommend_by_mood(cat, mood, k=10)
    mean = recs[feature].mean()
    assert check(mean), f"{mood}: mean {feature} = {mean:.2f}"


def test_opposite_moods_give_different_results(cat):
    _, calm = recommend_by_mood(cat, "sleep", k=10)
    _, hype = recommend_by_mood(cat, "workout", k=10)
    assert set(calm["title"]).isdisjoint(hype["title"])
    assert hype["energy"].mean() - calm["energy"].mean() > 0.4


def test_natural_sentences_work(cat):
    for text in ["I want a chill song to play in a cafe", "need something for the gym",
                 "sad rainy night", "music for a road trip"]:
        moods, recs = recommend_by_mood(cat, text, k=10)
        assert moods and len(recs) == 10, text


def test_results_are_deterministic(cat):
    _, a = recommend_by_mood(cat, "chill cafe", k=10)
    _, b = recommend_by_mood(cat, "chill cafe", k=10)
    assert list(a["title"]) == list(b["title"])
