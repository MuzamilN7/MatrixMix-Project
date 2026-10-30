import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        # TODO: Implement recommendation logic
        return self.songs[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        # TODO: Implement explanation logic
        return "Explanation placeholder"

def load_songs(csv_path: str) -> List[Dict]:
    """Read songs from a CSV file into dicts, converting numeric columns to int or float."""
    print(f"Loading songs from {csv_path}...")
    int_fields = ("id", "tempo_bpm")
    float_fields = ("energy", "valence", "danceability", "acousticness")

    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            for field in int_fields:
                row[field] = int(row[field])
            for field in float_fields:
                row[field] = float(row[field])
            songs.append(row)
    return songs

MOOD_POINTS = 3.0
GENRE_POINTS = 2.0

# feature -> (label, max points, range used to normalize the difference)
NUMERIC_FEATURES = {
    "energy": ("Energy", 1.5, 1.0),
    "valence": ("Valence", 0.5, 1.0),
    "tempo_bpm": ("Tempo", 0.5, 108.0),  # dataset range is 60 to 168 bpm
    "danceability": ("Danceability", 0.5, 1.0),
    "acousticness": ("Acousticness", 0.5, 1.0),
}

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Return a song's score and the list of reasons ("Mood match (+3)") that earned it."""
    score = 0.0
    reasons = []

    if "mood" in user_prefs and song["mood"] == user_prefs["mood"]:
        score += MOOD_POINTS
        reasons.append(f"Mood match (+{MOOD_POINTS:g})")

    if "genre" in user_prefs and song["genre"] == user_prefs["genre"]:
        score += GENRE_POINTS
        reasons.append(f"Genre match (+{GENRE_POINTS:g})")

    # Numeric features: full points for an exact hit, fewer the further away the song is.
    for feature, (label, points, span) in NUMERIC_FEATURES.items():
        if feature not in user_prefs:
            continue
        closeness = max(0.0, 1 - abs(song[feature] - user_prefs[feature]) / span)
        earned = points * closeness
        score += earned
        reasons.append(f"{label} closeness (+{earned:.2f})")

    return score, reasons

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """Score every song and return the top k as (song, score, explanation), best first."""
    scored = (
        (song, score, ", ".join(reasons))
        for song in songs
        for score, reasons in [score_song(user_prefs, song)]
    )
    return sorted(scored, key=lambda item: item[1], reverse=True)[:k]
