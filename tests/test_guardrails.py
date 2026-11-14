"""Tests for src/guardrails.py and the explicit-content filter."""
import pandas as pd
import pytest

from src.guardrails import (
    LOW_CONFIDENCE_MOOD,
    LOW_CONFIDENCE_SONG,
    MAX_QUERY_LEN,
    clean_query,
    confidence,
    verify_results,
)
from src.mood import recommend_by_mood
from src.similar import SongSimilarity, build_catalog


def good_list() -> pd.DataFrame:
    return pd.DataFrame({
        "title": ["A", "B", "C"], "artist": ["x", "y", "z"],
        "score": [0.9, 0.8, 0.7], "why": ["r1", "r2", "r3"],
    })


# ---------- clean_query (input validation) ----------

@pytest.mark.parametrize("raw", ["", "   ", "\n\t", None, 123, "!!!", "???---", "🎵🎵"])
def test_unusable_input_is_rejected_with_a_message(raw):
    qc = clean_query(raw)
    assert not qc.ok and qc.error


def test_normal_input_passes_unchanged():
    qc = clean_query("chill cafe")
    assert qc.ok and qc.text == "chill cafe" and qc.warnings == []


def test_control_characters_and_extra_spaces_are_cleaned():
    assert clean_query("  chill\x00\x07   cafe \n").text == "chill cafe"


def test_long_input_is_truncated_with_a_warning():
    qc = clean_query("a" * 1000)
    assert qc.ok and len(qc.text) <= MAX_QUERY_LEN and qc.warnings


def test_input_at_the_limit_is_not_truncated():
    qc = clean_query("a" * MAX_QUERY_LEN)
    assert len(qc.text) == MAX_QUERY_LEN and not qc.warnings


@pytest.mark.parametrize("raw", ["Señorita", "Beyoncé", "Café del Mar", "99 Problems"])
def test_accents_and_numbers_are_accepted(raw):
    assert clean_query(raw).ok


# ---------- verify_results (output self-check) ----------

def test_good_list_has_no_problems():
    assert verify_results(good_list(), k=10) == []


def test_empty_list_has_no_problems():
    assert verify_results(good_list().iloc[0:0], k=10) == []


def test_detects_duplicate_songs():
    bad = pd.concat([good_list(), good_list().iloc[[0]]], ignore_index=True)
    bad["score"] = sorted(bad["score"], reverse=True)
    assert any("twice" in p for p in verify_results(bad, k=10))


def test_detects_too_many_songs_by_one_artist():
    bad = good_list()
    bad["artist"] = "same"
    assert any("one artist" in p for p in verify_results(bad, k=10))


def test_detects_out_of_range_scores():
    bad = good_list()
    bad.loc[0, "score"] = 1.5
    assert any("outside 0-1" in p for p in verify_results(bad, k=10))


def test_detects_unsorted_results():
    bad = good_list().iloc[::-1].reset_index(drop=True)
    assert any("sorted" in p for p in verify_results(bad, k=10))


def test_detects_missing_explanations():
    bad = good_list()
    bad.loc[1, "why"] = "  "
    assert any("explanation" in p for p in verify_results(bad, k=10))


def test_detects_too_many_results():
    assert any("k=2" in p for p in verify_results(good_list(), k=2))


def test_detects_a_version_of_the_seed_song():
    bad = good_list()
    bad.loc[0, "title"] = "Heat Waves (with iann dior)"
    assert any("version of the song" in p for p in verify_results(bad, k=10, seed_title="Heat Waves"))


# ---------- confidence (weak-match warning) ----------

def test_strong_song_results_have_no_warning():
    assert confidence(good_list(), "song") is None


def test_weak_song_results_warn():
    weak = good_list()
    weak["score"] = [LOW_CONFIDENCE_SONG - 0.1] * 3
    assert "Low confidence" in confidence(weak, "song")


def test_weak_mood_results_warn():
    weak = good_list()
    weak["score"] = [LOW_CONFIDENCE_MOOD - 0.1] * 3
    assert "Low confidence" in confidence(weak, "mood")


def test_empty_results_get_a_message():
    assert confidence(good_list().iloc[0:0], "song")


# ---------- explicit filter ----------

def tiny_catalog() -> pd.DataFrame:
    def row(title, artist, explicit, i):
        return dict(title=title, artist=artist, genres=["pop"], year=2016, popularity=80, album="x",
                    image_url=None, spotify_id=f"id{i}", explicit=explicit, energy=0.9, valence=0.6,
                    acousticness=0.05, danceability=0.8, tempo=140.0, instrumentalness=0.0)
    return pd.DataFrame([row("Clean One", "a", False, 0), row("Dirty One", "b", True, 1),
                         row("Clean Two", "c", False, 2), row("Dirty Two", "d", True, 3)])


def test_clean_only_removes_explicit_songs_in_mood_mode():
    _, recs = recommend_by_mood(tiny_catalog(), "gym", k=10, clean_only=True)
    assert set(recs["title"]) == {"Clean One", "Clean Two"}


def test_explicit_songs_appear_when_filter_is_off():
    # Negative control: proves the filter above is what removes them.
    _, recs = recommend_by_mood(tiny_catalog(), "gym", k=10, clean_only=False)
    assert {"Dirty One", "Dirty Two"} <= set(recs["title"])


def test_clean_only_removes_explicit_songs_in_song_mode():
    m = SongSimilarity(tiny_catalog())
    assert set(m.recommend(0, k=10, clean_only=True)["title"]) == {"Clean Two"}
    assert {"Dirty One", "Dirty Two"} <= set(m.recommend(0, k=10, clean_only=False)["title"])


@pytest.fixture(scope="module")
def real_cat():
    return build_catalog()


def test_real_catalog_has_explicit_flags(real_cat):
    assert real_cat["explicit"].dtype == bool
    assert 1000 < real_cat["explicit"].sum() < 3000


def test_real_data_clean_only_never_leaks_explicit_songs(real_cat):
    for text in ["gym workout", "party", "angry", "sad", "chill cafe", "road trip"]:
        _, recs = recommend_by_mood(real_cat, text, k=10, clean_only=True)
        assert not recs["explicit"].any(), text


def test_real_data_explicit_songs_do_exist_without_the_filter(real_cat):
    # Negative control on real data: a high-energy mood does return explicit songs when unfiltered.
    _, recs = recommend_by_mood(real_cat, "angry", k=50, clean_only=False)
    assert recs["explicit"].any()
