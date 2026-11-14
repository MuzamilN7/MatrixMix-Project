"""Keyword-based mood search: turn text like "a chill song for a cafe" into audio-feature targets
and rank songs by how close their features are."""
import re

import numpy as np
import pandas as pd

# Each keyword maps to target audio features (0-1, tempo in bpm) and optional genre hints.
# Several matched keywords are averaged, so "chill cafe" blends both profiles.
PROFILES = {
    "chill":    dict(energy=0.30, valence=0.50, acousticness=0.60, danceability=0.55, tempo=90,
                     genres=["lo-fi", "chillwave", "bossa nova", "downtempo", "chill", "indie"]),
    "cafe":     dict(energy=0.35, valence=0.60, acousticness=0.70, danceability=0.55, tempo=95,
                     genres=["jazz", "bossa nova", "acoustic", "folk", "singer-songwriter", "soul"]),
    "study":    dict(energy=0.25, valence=0.40, acousticness=0.60, danceability=0.45, tempo=85, instrumentalness=0.6,
                     genres=["lo-fi", "ambient", "classical", "instrumental"]),
    "sleep":    dict(energy=0.12, valence=0.30, acousticness=0.85, danceability=0.30, tempo=70,
                     genres=["ambient", "classical", "new age"]),
    "relax":    dict(energy=0.30, valence=0.55, acousticness=0.65, danceability=0.50, tempo=90,
                     genres=["acoustic", "chill", "soft"]),
    "romantic": dict(energy=0.40, valence=0.50, acousticness=0.55, danceability=0.55, tempo=95,
                     genres=["r&b", "soul", "adult standards", "love"]),
    "sad":      dict(energy=0.30, valence=0.15, acousticness=0.60, danceability=0.40, tempo=85,
                     genres=["sad", "singer-songwriter", "emo"]),
    "happy":    dict(energy=0.75, valence=0.85, acousticness=0.20, danceability=0.75, tempo=120,
                     genres=["pop", "dance pop", "funk"]),
    "party":    dict(energy=0.85, valence=0.75, acousticness=0.10, danceability=0.85, tempo=125,
                     genres=["dance", "edm", "hip hop", "reggaeton", "pop"]),
    "workout":  dict(energy=0.90, valence=0.65, acousticness=0.08, danceability=0.75, tempo=140,
                     genres=["edm", "hip hop", "rock", "trap"]),
    "road trip": dict(energy=0.70, valence=0.70, acousticness=0.25, danceability=0.60, tempo=115,
                      genres=["rock", "country", "pop rock", "classic rock"]),
    "angry":    dict(energy=0.92, valence=0.30, acousticness=0.05, danceability=0.50, tempo=140,
                     genres=["metal", "hard rock", "punk", "rap"]),
    "focus":    dict(energy=0.35, valence=0.45, acousticness=0.50, danceability=0.50, tempo=95, instrumentalness=0.5,
                     genres=["lo-fi", "instrumental", "ambient"]),
    "dance":    dict(energy=0.80, valence=0.70, acousticness=0.10, danceability=0.90, tempo=124,
                     genres=["dance pop", "edm", "house", "disco"]),
}

# Alternate words that point to a profile above.
ALIASES = {
    "chill": ["chill", "chilled", "mellow", "laid back", "laidback", "calm", "easygoing", "soft", "smooth"],
    "cafe": ["cafe", "café", "coffee", "coffee shop", "restaurant", "brunch", "bookstore"],
    "study": ["study", "studying", "homework", "reading", "library"],
    "sleep": ["sleep", "sleeping", "bedtime", "lullaby"],
    "relax": ["relax", "relaxing", "unwind", "spa", "peaceful"],
    "romantic": ["romantic", "romance", "date", "love", "dinner"],
    "sad": ["sad", "melancholy", "heartbreak", "breakup", "cry", "lonely", "rainy"],
    "happy": ["happy", "upbeat", "cheerful", "sunny", "feel good", "feel-good", "fun"],
    "party": ["party", "club", "celebrate", "pregame"],
    "workout": ["workout", "gym", "run", "running", "cardio", "lifting", "hype", "pump"],
    "road trip": ["road trip", "roadtrip", "driving", "drive", "car"],
    "angry": ["angry", "aggressive", "rage", "intense"],
    "focus": ["focus", "concentrate", "work", "coding", "deep work"],
    "dance": ["dance", "dancing", "groove"],
}

# Feature -> (weight, span used to normalize the distance)
WEIGHTS = {
    "energy": (1.5, 1.0),
    "valence": (1.0, 1.0),
    "acousticness": (1.2, 1.0),
    "danceability": (0.8, 1.0),
    "tempo": (0.6, 100.0),
    "instrumentalness": (0.8, 1.0),
}
GENRE_BONUS = 0.10  # fraction of the max score added when a song's genres hit a hint
POP_BONUS = 0.05
MAX_PER_ARTIST = 2


def parse_mood(text: str) -> list[str]:
    """Return the profile names mentioned in `text` (longest aliases matched first)."""
    t = " " + re.sub(r"[^a-z0-9é&' -]", " ", text.lower()) + " "
    found = []
    for name, words in ALIASES.items():
        if any(re.search(rf"(?<![a-z]){re.escape(w)}(?![a-z])", t) for w in words):
            found.append(name)
    return found


def build_target(moods: list[str]) -> tuple[dict, list[str]]:
    """Average the feature targets of the matched moods and union their genre hints."""
    target, genres = {}, []
    for feat in WEIGHTS:
        vals = [PROFILES[m][feat] for m in moods if feat in PROFILES[m]]
        if vals:
            target[feat] = float(np.mean(vals))
    for m in moods:
        genres += [g for g in PROFILES[m]["genres"] if g not in genres]
    return target, genres


def recommend_by_mood(cat: pd.DataFrame, text: str, k: int = 10, clean_only: bool = False):
    """Rank songs by closeness to the mood in `text`. Returns (moods, dataframe) — empty if no keyword matched."""
    moods = parse_mood(text)
    if not moods:
        return moods, cat.iloc[0:0]

    target, hints = build_target(moods)
    has = cat["energy"].notna().values  # only songs with audio features
    score = np.zeros(len(cat))
    total = 0.0
    for feat, goal in target.items():
        w, span = WEIGHTS[feat]
        vals = cat[feat].fillna(goal).values
        score += w * np.clip(1 - np.abs(vals - goal) / span, 0, 1)
        total += w
    score /= total

    hint_hit = np.array([any(h in g or g in h for g in gs for h in hints) for gs in cat["genres"]])
    score = score + GENRE_BONUS * hint_hit + POP_BONUS * (cat["popularity"].values / 100)
    score /= 1 + GENRE_BONUS + POP_BONUS  # scale to 0-1 so the displayed similarity is meaningful
    score[~has] = -1
    if clean_only and "explicit" in cat.columns:
        score[cat["explicit"].fillna(False).astype(bool).values] = -1

    top, per_artist = [], {}
    for i in np.argsort(-score):
        if score[i] < 0 or len(top) == k:
            break
        a = cat["artist"].iloc[i]
        if per_artist.get(a, 0) >= MAX_PER_ARTIST:
            continue
        per_artist[a] = per_artist.get(a, 0) + 1
        top.append(i)

    out = cat.iloc[top].copy()
    out["score"] = score[top]
    out["why"] = [
        f"energy {r.energy:.2f}, acoustic {r.acousticness:.2f}, tempo {r.tempo:.0f} bpm"
        + ("; fits genre" if hint_hit[i] else "")
        for i, r in zip(top, out.itertuples())
    ]
    return moods, out
