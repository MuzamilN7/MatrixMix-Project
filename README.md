# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

---

## How The System Works

Real-world recommenders such as Spotify or YouTube combine two ideas. Collaborative filtering looks at what millions of similar listeners played, skipped, or saved. Content-based filtering compares the attributes of the songs themselves, such as audio features, genre, and mood, to what a listener has liked. They then score a huge catalog, rank it, and add diversity and freshness rules on top. My version is a small content-based recommender. It has no listening history from other users, so it will prioritize **how close a song's vibe is to what the user says they want**. Numeric features (energy) are scored by closeness to a target, not "higher is better". Mood and genre add points for exact matches, and numeric closeness fills the rest of a 10-point score.

**Song features** (from `data/songs.csv`)

- Used in scoring: `mood`, `genre`, `energy`, `valence`, `tempo_bpm`, `danceability`, `acousticness`
- Identifiers for display: `id`, `title`, `artist`

**UserProfile features**

- `favorite_mood` and `favorite_genre`: categorical targets that earn points on an exact match
- `target_energy`, `target_valence`, `target_danceability`, `target_acousticness`: desired levels (0-1)
- `target_tempo_bpm`: desired tempo in beats per minute

**Algorithm Recipe**

Each song gets a score out of 10. Every feature is scored from 0 to 1, multiplied by its weight, and summed.

| Feature | Weight | Feature score (0 to 1) |
|---|---|---|
| mood | 3.0 | 1 if exact match, else 0 |
| genre | 2.0 | 1 if exact match, else 0 |
| energy | 2.0 | `1 - abs(song - target)` |
| valence | 1.5 | `1 - abs(song - target)` |
| tempo | 0.5 | `1 - abs(song - target) / 108` (dataset range is 60 to 168 bpm) |
| danceability | 0.5 | `1 - abs(song - target)` |
| acousticness | 0.5 | `1 - abs(song - target)` |

- **Scoring rule (one song):** `score = sum(weight * feature_score)`. Numeric features use closeness to the target, so a user who wants 0.3 energy is not pushed toward 0.9.
- **Ranking rule (all songs):** score every song, sort from highest to lowest, and return the top `k`, each with a short explanation of which features contributed most.

**Why these weights**

- **Mood (3) above genre (2):** mood describes what the listener wants right now, while genre is a standing taste. A chill jazz track can satisfy a chill lofi fan, but rarely the other way around.
- **Valence (1.5) above tempo (0.5):** valence separates songs that energy cannot (Storm Runner and Afterglow Static have similar energy but opposite feel), while tempo mostly repeats energy.
- **Categorical points total 5 of 10**, so numeric closeness can still beat a single lucky match.

**Expected biases**

- **Mood can overshadow good numeric fits.** Mood is worth 3 points, so a song with the right mood but the wrong energy and valence can outrank a song that fits every number but has a different mood label.
- **Exact-match labels are brittle.** Related moods (chill, relaxed, focused) score 0 against each other, so Coffee Shop Stories gets no mood credit for a "chill" user even though it is a close fit.
- **Genre favors the few well-represented genres.** Lofi has 3 songs and pop has 2, while most other genres have 1. A lofi fan gets several genre matches, and a metal or classical fan gets at most one, so their lists fill with weaker numeric matches.
- **Small catalog, small pool.** With 18 songs, a niche profile will see the same few songs at the top.
- **Closeness treats all directions equally.** A song 0.2 too high in energy scores the same as one 0.2 too low, even though a user may care more about one direction.
- **Valence is only a proxy for mood.** An "angry" user may type a low valence target, which also rewards sad, quiet songs like Moonlit Sonata, even though their energy is nothing alike.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Sample Recommendation Output

Paste a sample of your recommender's output here as a text block so a reader can see what it produces:

```
# e.g.:
# User profile: genre=indie, mood=chill, energy=low
# Recommendations:
#   1. ...
#   2. ...
#   3. ...
```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this



