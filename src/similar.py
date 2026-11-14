"""Song-to-song recommender built from the Spotify top-1000 CSV and the MusicOSet metadata CSVs.

Neither dataset has audio features, so "closest" is measured with metadata:
genre overlap (from the artists' genres), same artist, release year, and popularity.
"""
import ast
import re
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MUSICOSET = DATA_DIR / "musicoset_metadata"

# Weights for the final similarity score (sum to 1).
W_GENRE, W_ARTIST, W_YEAR, W_POP = 0.55, 0.15, 0.20, 0.10
FEATURES = DATA_DIR / "musicoset_songfeatures" / "acoustic_features.csv"
AUDIO_FEATURES = ["energy", "valence", "acousticness", "danceability", "tempo", "instrumentalness"]
MAX_PER_ARTIST = 2
YEAR_SPAN = 15.0  # years apart at which year similarity hits 0


def _parse(value, default):
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return default


def _norm(text: str) -> str:
    """Lowercase, turn hyphens/slashes into spaces, drop other punctuation, collapse spaces."""
    text = re.sub(r"[-/_]", " ", str(text).lower())
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", text)).strip()


def build_catalog() -> pd.DataFrame:
    """Merge both datasets into one table: title, artist, genres, year, popularity, album, image_url, spotify_id."""
    songs = pd.read_csv(MUSICOSET / "songs.csv", sep="\t")
    tracks = pd.read_csv(MUSICOSET / "tracks.csv", sep="\t")
    albums = pd.read_csv(MUSICOSET / "albums.csv", sep="\t")
    artists = pd.read_csv(MUSICOSET / "artists.csv", sep="\t")
    top = pd.read_csv(DATA_DIR / "spotify_top_1000_tracks.csv")

    artist_genres = {
        row.artist_id: _parse(row.genres, []) for row in artists.itertuples()
    }
    genres_by_name = {_norm(r.name): _parse(r.genres, []) for r in artists.itertuples()}

    # --- MusicOSet songs -> artists, album, cover art
    songs["artist_map"] = songs["artists"].map(lambda v: _parse(v, {}))
    songs["artist"] = songs["artist_map"].map(lambda m: ", ".join(m.values()))
    songs["genres"] = songs["artist_map"].map(
        lambda m: sorted({g for a in m for g in artist_genres.get(a, [])})
    )
    # A song can sit on several albums; keep the first listing.
    tracks = tracks.drop_duplicates("song_id")
    albums = albums.drop_duplicates("album_id").rename(columns={"name": "album"})
    m = songs.merge(tracks[["song_id", "album_id", "release_date"]], on="song_id", how="left")
    m = m.merge(albums[["album_id", "album", "image_url"]], on="album_id", how="left")
    m["year"] = pd.to_datetime(m["release_date"], errors="coerce").dt.year
    ms = m.rename(columns={"song_name": "title", "song_id": "spotify_id"})[
        ["title", "artist", "genres", "year", "popularity", "album", "image_url", "spotify_id", "explicit"]
    ]

    # --- Spotify top 1000 (adds songs MusicOSet lacks; genres borrowed from artist-name match)
    top = top[~top["id"].isin(ms["spotify_id"])].copy()
    top["genres"] = top["artist"].map(lambda a: genres_by_name.get(_norm(a.split(",")[0]), []))
    top["year"] = pd.to_datetime(top["release_date"], errors="coerce").dt.year
    top["image_url"] = None
    top["explicit"] = False  # the Spotify CSV has no explicit flag; treated as unknown (not filtered)
    tp = top.rename(columns={"track_name": "title", "id": "spotify_id", "album": "album"})[
        ["title", "artist", "genres", "year", "popularity", "album", "image_url", "spotify_id", "explicit"]
    ]

    cat = pd.concat([ms, tp], ignore_index=True)

    # Audio features exist only for MusicOSet songs; others stay NaN (and are skipped by mood search).
    feats = pd.read_csv(FEATURES, sep="\t")[["song_id", *AUDIO_FEATURES]]
    cat = cat.merge(feats, left_on="spotify_id", right_on="song_id", how="left").drop(columns="song_id")
    cat["tempo"] = cat["tempo"].replace(0, np.nan)  # a tempo of 0 is missing data, not a real tempo
    cat["key"] = cat["title"].map(_norm) + "|" + cat["artist"].map(_norm)
    cat = cat.drop_duplicates("key").reset_index(drop=True)
    cat["explicit"] = cat["explicit"].fillna(False).astype(bool)
    cat["year"] = cat["year"].fillna(cat["year"].median())
    cat["popularity"] = cat["popularity"].fillna(cat["popularity"].median())
    return cat


class SongSimilarity:
    def __init__(self, catalog: pd.DataFrame | None = None):
        self.cat = catalog if catalog is not None else build_catalog()
        vocab = sorted({g for gs in self.cat["genres"] for g in gs})
        idx = {g: i for i, g in enumerate(vocab)}
        mat = np.zeros((len(self.cat), len(vocab)), dtype=np.float32)
        for r, gs in enumerate(self.cat["genres"]):
            for g in gs:
                mat[r, idx[g]] = 1.0
        # IDF weighting so rare genres ("vaporwave") count more than "pop".
        df = mat.sum(axis=0)
        idf = np.log((1 + len(mat)) / (1 + df)) + 1
        mat *= idf
        norms = np.linalg.norm(mat, axis=1, keepdims=True)
        norms[norms == 0] = 1
        self.genre_mat = mat / norms
        self.titles_norm = self.cat["title"].map(_norm)
        # Title without "(with X)" / "- Remastered" suffixes, to spot other versions of a song.
        self.base_titles = self.cat["title"].map(lambda t: _norm(re.split(r" \(| - ", t)[0]))
        self.artists_norm = self.cat["artist"].map(_norm)
        self.artist_sets = [set(_norm(a) for a in s.split(",")) for s in self.cat["artist"]]

    def search(self, query: str, limit: int = 15) -> pd.DataFrame:
        """Songs whose title (or 'title artist') contains the query, most popular first."""
        q = _norm(query)
        if not q:
            return self.cat.iloc[0:0]
        hay = self.titles_norm + " " + self.artists_norm
        hits = self.cat[hay.str.contains(q, regex=False)]
        return hits.sort_values("popularity", ascending=False).head(limit)

    def recommend(self, index: int, k: int = 10, clean_only: bool = False) -> pd.DataFrame:
        """Return the k songs most similar to catalog row `index`, with a `score` column.

        clean_only=True hides songs flagged explicit in MusicOSet.
        """
        c = self.cat
        genre = self.genre_mat @ self.genre_mat[index]
        year = np.clip(1 - np.abs(c["year"].values - c["year"].iloc[index]) / YEAR_SPAN, 0, 1)
        pop = 1 - np.abs(c["popularity"].values - c["popularity"].iloc[index]) / 100
        base = self.artist_sets[index]
        same_artist = np.array([1.0 if s & base else 0.0 for s in self.artist_sets])

        score = W_GENRE * genre + W_ARTIST * same_artist + W_YEAR * year + W_POP * pop
        score = np.clip(score, 0.0, 1.0)  # float rounding can push a perfect match to 1.0000001
        score[index] = -1
        if clean_only and "explicit" in self.cat.columns:
            score[self.cat["explicit"].values] = -1
        # Hide other copies of the same song (remasters, re-releases).
        score[(self.base_titles == self.base_titles.iloc[index]).values] = -1

        # Cap songs per artist so one artist can't fill the whole list.
        top, per_artist = [], {}
        for i in np.argsort(-score):
            if score[i] < 0 or len(top) == k:
                break
            a = self.artists_norm.iloc[i]
            if per_artist.get(a, 0) >= MAX_PER_ARTIST:
                continue
            per_artist[a] = per_artist.get(a, 0) + 1
            top.append(i)
        out = c.iloc[top].copy()
        out["score"] = score[top]
        out["why"] = [self._why(index, i, genre[i], same_artist[i]) for i in top]
        return out

    def _why(self, a: int, b: int, genre_sim: float, same_artist: float) -> str:
        shared = sorted(set(self.cat["genres"].iloc[a]) & set(self.cat["genres"].iloc[b]))
        parts = []
        if same_artist:
            parts.append("same artist")
        if shared:
            parts.append("shared genres: " + ", ".join(shared[:3]))
        ya, yb = int(self.cat["year"].iloc[a]), int(self.cat["year"].iloc[b])
        album_a, album_b = self.cat["album"].iloc[a], self.cat["album"].iloc[b]
        same_album = isinstance(album_a, str) and album_a == album_b
        if same_album or ya == yb:
            parts.append(f"same era ({yb})")
        elif abs(ya - yb) <= 3:
            parts.append(f"similar era ({yb})")
        return "; ".join(parts) or "similar popularity"
