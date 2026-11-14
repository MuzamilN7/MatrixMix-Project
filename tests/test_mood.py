"""Tests for src/mood.py: keyword parsing, target building and mood ranking."""
import numpy as np
import pandas as pd
import pytest

from src.mood import ALIASES, PROFILES, build_target, parse_mood, recommend_by_mood


def make_catalog() -> pd.DataFrame:
    """Tiny catalog with clearly chill, clearly intense, and one song without audio features."""
    rows = [
        # title, artist, genres, energy, valence, acoustic, dance, tempo, instr, pop
        ("Quiet Cafe",    "A", ["jazz"],  0.30, 0.55, 0.70, 0.55, 92,  0.1, 60),
        ("Soft Morning",  "B", ["folk"],  0.33, 0.60, 0.68, 0.50, 95,  0.0, 55),
        ("Warm Cup",      "C", ["bossa nova"], 0.35, 0.58, 0.72, 0.55, 90, 0.2, 50),
        ("Loud Gym",      "D", ["edm"],   0.95, 0.65, 0.03, 0.80, 145, 0.0, 70),
        ("Metal Storm",   "E", ["metal"], 0.97, 0.20, 0.02, 0.40, 150, 0.0, 65),
        ("No Features",   "F", ["jazz"],  np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, 99),
    ]
    return pd.DataFrame(
        [
            dict(title=t, artist=a, genres=g, year=2000, popularity=p, album="x", image_url=None,
                 spotify_id=f"id{i}", energy=e, valence=v, acousticness=ac, danceability=d,
                 tempo=tp, instrumentalness=ins)
            for i, (t, a, g, e, v, ac, d, tp, ins, p) in enumerate(rows)
        ]
    )


# ---------- parse_mood ----------

def test_parse_single_keyword():
    assert parse_mood("chill") == ["chill"]


def test_parse_sentence_with_two_moods():
    assert parse_mood("I want a chill song to play in a cafe") == ["chill", "cafe"]


@pytest.mark.parametrize("text,expected", [
    ("gym", "workout"), ("lifting weights", "workout"), ("rainy day", "sad"),
    ("coffee shop vibes", "cafe"), ("late night studying", "study"), ("road trip", "road trip"),
])
def test_aliases_map_to_profile(text, expected):
    assert expected in parse_mood(text)


def test_parse_is_case_insensitive():
    assert parse_mood("CHILL CAFE") == ["chill", "cafe"]


def test_parse_ignores_partial_words():
    # "car" inside "scarlet" and "run" inside "brunch" must not trigger road trip / workout.
    assert "road trip" not in parse_mood("scarlet")
    assert "workout" not in parse_mood("brunch")


@pytest.mark.parametrize("text", ["", "   ", "xyz", "12345", "!!!"])
def test_parse_unknown_text_returns_empty(text):
    assert parse_mood(text) == []


def test_every_alias_group_has_a_profile():
    assert set(ALIASES) == set(PROFILES)


# ---------- build_target ----------

def test_target_for_single_mood_matches_profile():
    target, genres = build_target(["workout"])
    assert target["energy"] == PROFILES["workout"]["energy"]
    assert genres == PROFILES["workout"]["genres"]


def test_target_averages_multiple_moods():
    target, _ = build_target(["chill", "cafe"])
    expected = (PROFILES["chill"]["energy"] + PROFILES["cafe"]["energy"]) / 2
    assert target["energy"] == pytest.approx(expected)


def test_target_genres_have_no_duplicates():
    _, genres = build_target(["chill", "relax", "cafe"])
    assert len(genres) == len(set(genres))


def test_profiles_have_valid_ranges():
    for name, p in PROFILES.items():
        for feat in ("energy", "valence", "acousticness", "danceability"):
            assert 0 <= p[feat] <= 1, f"{name}.{feat}"
        assert 40 <= p["tempo"] <= 200, f"{name}.tempo"


# ---------- recommend_by_mood ----------

def test_chill_query_ranks_chill_songs_first():
    moods, recs = recommend_by_mood(make_catalog(), "chill cafe", k=3)
    assert set(recs["title"]) == {"Quiet Cafe", "Soft Morning", "Warm Cup"}


def test_workout_query_ranks_high_energy_first():
    _, recs = recommend_by_mood(make_catalog(), "gym", k=2)
    assert recs.iloc[0]["title"] in {"Loud Gym", "Metal Storm"}
    assert "Quiet Cafe" not in set(recs["title"])


def test_songs_without_audio_features_are_skipped():
    _, recs = recommend_by_mood(make_catalog(), "chill", k=10)
    assert "No Features" not in set(recs["title"])


def test_unknown_mood_returns_empty_result():
    moods, recs = recommend_by_mood(make_catalog(), "xyz", k=10)
    assert moods == [] and recs.empty


def test_scores_are_between_0_and_1_and_sorted():
    _, recs = recommend_by_mood(make_catalog(), "chill", k=10)
    assert recs["score"].between(0, 1).all()
    assert list(recs["score"]) == sorted(recs["score"], reverse=True)


def test_k_limits_number_of_results():
    _, recs = recommend_by_mood(make_catalog(), "chill", k=2)
    assert len(recs) == 2


def test_at_most_two_songs_per_artist():
    cat = make_catalog()
    extra = pd.concat([cat.iloc[[0]]] * 4, ignore_index=True)  # 4 more copies of artist "A"
    extra["title"] = [f"Copy {i}" for i in range(4)]
    big = pd.concat([cat, extra], ignore_index=True)
    _, recs = recommend_by_mood(big, "chill cafe", k=10)
    assert recs["artist"].value_counts().max() <= 2


def test_every_result_has_an_explanation():
    _, recs = recommend_by_mood(make_catalog(), "chill", k=3)
    assert all(isinstance(w, str) and w for w in recs["why"])
