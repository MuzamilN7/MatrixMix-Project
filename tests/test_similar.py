"""Tests for src/similar.py: the song-to-song recommender (small catalog) and the real merged catalog."""
import numpy as np
import pandas as pd
import pytest

from src.similar import SongSimilarity


def song(title, artist, genres, year=2016, pop=80, album="Album", i=0):
    return dict(title=title, artist=artist, genres=genres, year=year, popularity=pop, album=album,
                image_url=None, spotify_id=f"id{i}", energy=0.5, valence=0.5, acousticness=0.5,
                danceability=0.5, tempo=100.0, instrumentalness=0.0)


def make_model() -> SongSimilarity:
    rows = [
        song("Seed Song",       "Star",  ["pop", "r&b"],        2016, 90, "Seed Album", 0),
        song("Same Artist 1",   "Star",  ["pop", "r&b"],        2016, 85, "Seed Album", 1),
        song("Same Artist 2",   "Star",  ["pop", "r&b"],        2016, 85, "Other",      2),
        song("Same Artist 3",   "Star",  ["pop", "r&b"],        2016, 85, "Other",      3),
        song("Genre Twin",      "Other", ["pop", "r&b"],        2016, 80, "Twin Album", 4),
        song("Genre Half",      "Third", ["pop"],               2015, 70, "Third LP",   5),
        song("Metal Track",     "Heavy", ["metal"],             1985, 40, "Loud",       6),
        song("Seed Song (with Guest)", "Guest", ["pop", "r&b"], 2016, 80, "Remix",      7),
    ]
    return SongSimilarity(pd.DataFrame(rows))


# ---------- search ----------

def test_search_finds_by_title_case_insensitive():
    m = make_model()
    assert m.search("seed song").iloc[0]["title"].startswith("Seed Song")


def test_search_finds_by_artist():
    assert not make_model().search("heavy").empty


def test_search_ignores_punctuation_and_blank_queries():
    m = make_model()
    assert not m.search("Seed-Song!!").empty
    assert m.search("").empty and m.search("   ").empty


def test_search_no_match_is_empty():
    assert make_model().search("zzzqqq").empty


def test_search_results_sorted_by_popularity():
    hits = make_model().search("a")
    assert list(hits["popularity"]) == sorted(hits["popularity"], reverse=True)


# ---------- recommend ----------

def test_recommend_never_returns_the_seed_song():
    m = make_model()
    recs = m.recommend(0, k=10)
    assert "Seed Song" not in set(recs["title"])


def test_recommend_hides_other_versions_of_the_seed():
    recs = make_model().recommend(0, k=10)
    assert "Seed Song (with Guest)" not in set(recs["title"])


def test_recommend_respects_k():
    assert len(make_model().recommend(0, k=2)) == 2


def test_scores_sorted_descending_and_in_range():
    recs = make_model().recommend(0, k=10)
    assert list(recs["score"]) == sorted(recs["score"], reverse=True)
    assert recs["score"].between(0, 1).all()


def test_similar_genre_beats_unrelated_genre():
    recs = make_model().recommend(0, k=10)
    titles = list(recs["title"])
    assert titles.index("Genre Twin") < titles.index("Metal Track")


def test_artist_cap_limits_songs_per_artist():
    recs = make_model().recommend(0, k=10)
    assert recs["artist"].value_counts().max() <= 2


def test_same_album_is_labeled_same_era():
    recs = make_model().recommend(0, k=10)
    why = recs[recs["title"] == "Same Artist 1"].iloc[0]["why"]
    assert "same era" in why and "same artist" in why


def test_different_year_within_3_is_similar_era():
    recs = make_model().recommend(0, k=10)
    why = recs[recs["title"] == "Genre Half"].iloc[0]["why"]
    assert "similar era" in why


def test_every_recommendation_has_a_reason():
    recs = make_model().recommend(0, k=10)
    assert all(isinstance(w, str) and w for w in recs["why"])


def test_song_with_no_genres_still_gets_recommendations():
    rows = [song("Lonely", "Nobody", [], i=0), song("Other", "Else", ["pop"], i=1)]
    recs = SongSimilarity(pd.DataFrame(rows)).recommend(0, k=5)
    assert len(recs) == 1


# ---------- real merged catalog (integration: how it behaves on regular use) ----------

@pytest.fixture(scope="module")
def real():
    return SongSimilarity()


def test_catalog_is_large_and_has_required_columns(real):
    cat = real.cat
    assert len(cat) > 20000
    for col in ["title", "artist", "genres", "year", "popularity", "album", "image_url",
                "spotify_id", "energy", "valence", "acousticness", "tempo"]:
        assert col in cat.columns


def test_catalog_has_no_duplicate_songs(real):
    assert real.cat["key"].is_unique


def test_catalog_has_no_missing_year_or_popularity(real):
    assert real.cat["year"].notna().all() and real.cat["popularity"].notna().all()


def test_audio_features_are_in_valid_ranges(real):
    cat = real.cat
    for feat in ["energy", "valence", "acousticness", "danceability"]:
        vals = cat[feat].dropna()
        assert vals.between(0, 1).all(), feat
    assert cat["tempo"].dropna().between(30, 260).all()


def test_most_songs_have_audio_features_and_covers(real):
    assert real.cat["energy"].notna().mean() > 0.9
    assert real.cat["image_url"].notna().mean() > 0.4  # the rest fall back to Spotify oEmbed


def test_popular_songs_can_be_found_and_recommended(real):
    for query in ["Starboy", "Heat Waves", "Blinding Lights", "Shape of You", "Bad Guy"]:
        hits = real.search(query)
        assert not hits.empty, query
        recs = real.recommend(hits.index[0], k=10)
        assert len(recs) == 10, query


def test_real_recommendations_follow_the_rules(real):
    rng = np.random.default_rng(0)
    for idx in rng.choice(len(real.cat), size=40, replace=False):
        recs = real.recommend(int(idx), k=10)
        assert 0 < len(recs) <= 10
        assert idx not in recs.index
        assert recs["artist"].str.lower().value_counts().max() <= 2
        assert recs["score"].between(0, 1).all()
        assert list(recs["score"]) == sorted(recs["score"], reverse=True)
        assert recs["why"].map(bool).all()


def test_starboy_recommendations_are_related(real):
    seed = real.search("Starboy").index[0]
    recs = real.recommend(seed, k=10)
    # at least some results should share a pop/r&b genre with the seed
    seed_genres = set(real.cat.loc[seed, "genres"])
    overlap = [len(seed_genres & set(g)) > 0 for g in recs["genres"]]
    assert sum(overlap) >= 7
