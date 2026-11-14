# 🎵 MatrixMix

**Give it a song or describe a vibe, and it returns the 10 closest songs, with album covers, a short reason for each pick, and a 10-second preview.**

## Original Project (Modules 1-3)

MatrixMix grew out of my **Music Recommender Simulation** (model name *VibeMatch 1.0*). That project was a small content-based recommender over a hand-made catalog of 18 songs (`data/songs.csv`). A user described a favorite mood, a favorite genre, and target levels for energy, valence, tempo, danceability and acousticness. Each song earned points for a mood match (3), a genre match (2), and numeric closeness to the targets, and the top 5 were returned with a plain-language explanation of the points. It still lives in `src/recommender.py` and `src/main.py`.

## Title and Summary

**MatrixMix** scales that idea up to real data and a real interface. It merges two datasets into a catalog of about 21,000 songs and offers two ways to find music:

- **A song I like:** type a song, and get the 10 most similar songs.
- **A mood or vibe:** type something like *"a chill song to play in a cafe"*, and get songs whose audio features fit that mood.

**Why it matters:** recommenders decide what people hear, so it is useful to build one where every ranking can be explained. Every result shows *why* it was picked (shared genres, same era, or the exact energy / acousticness / tempo that matched), instead of being a black box.

## Architecture Overview

The full diagram is in [`diagram/system_diagram.mmd`](diagram/system_diagram.mmd). In short, data flows **input → process → output**, with checks at the end:

1. **Input (Streamlit UI, `app.py`):** the user searches for a song or types a mood.
2. **Data and catalog (`src/similar.py`):** three CSV sources (Spotify top 1000, MusicOSet metadata, MusicOSet acoustic features) are merged and de-duplicated into one catalog of ~21k songs.
3. **Process:**
   - *Retriever:* `search()` finds the song the user meant by title or artist.
   - *Song recommender:* scores every song against the seed by genre overlap (55%), era (20%), same artist (15%) and popularity (10%).
   - *Mood parser + recommender (`src/mood.py`):* turns keywords into target audio features, then ranks songs by closeness to that target.
   - *Rules:* at most 2 songs per artist, and other versions of the seed song are hidden.
4. **Output:** the top 10 songs, each with a similarity score and a "why" line, an album cover (MusicOSet image, falling back to Spotify oEmbed), and a 10-second preview (iTunes Search API).
5. **Human and testing checks:** the user listens to the preview and judges the match; the developer spot-checks results and tunes weights and keywords; `pytest` and manual sample queries verify the code.

## Setup Instructions

1. **Clone the repo and enter the project folder:**
   ```bash
   git clone https://github.com/MuzamilN7/MatrixMix-Project.git
   cd MatrixMix-Project
   ```
2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Check the data is in place.** The app expects these under `data/`:
   - `spotify_top_1000_tracks.csv`
   - `musicoset_metadata/` (songs, tracks, albums, artists CSVs)
   - `musicoset_songfeatures/acoustic_features.csv`

   `lyrics.csv` is not needed and is excluded from git because it is over GitHub's 100 MB limit.
5. **Run the web app:**
   ```bash
   streamlit run app.py
   ```
   It opens at http://localhost:8501. The first load takes a few seconds while the catalog is built.
6. **(Optional) Run the original command-line recommender:**
   ```bash
   python src/main.py
   ```

Album covers and previews load from the internet, so you need a connection for those.

## Sample Interactions

These are real outputs from the system.

### 1. Song mode: input `Starboy` (The Weeknd, 2016)

| # | Song | Artist | Similarity | Why |
|---|---|---|---|---|
| 1 | Stargirl Interlude | The Weeknd | 0.98 | same artist; shared genres: canadian contemporary r&b, canadian pop, pop; same era (2016) |
| 2 | Die For You | The Weeknd | 0.98 | same artist; shared genres: canadian contemporary r&b, canadian pop, pop; same era (2016) |
| 3 | Scars To Your Beautiful | Alessia Cara | 0.60 | shared genres: canadian contemporary r&b, pop; same era (2016) |
| 4 | Here | Alessia Cara | 0.59 | shared genres: canadian contemporary r&b, pop; same era (2016) |
| 5 | Love Yourself | Justin Bieber | 0.53 | shared genres: canadian pop, pop; similar era (2015) |

### 2. Mood mode: input `a chill song to play in a cafe`

Detected moods: **chill, cafe** (blended into a target of roughly energy 0.33, acousticness 0.65, tempo 92 bpm).

| # | Song | Artist | Similarity | Why |
|---|---|---|---|---|
| 1 | Make It with You | Bread | 0.94 | energy 0.36, acoustic 0.66, tempo 84 bpm; fits genre |
| 2 | Too Many Rivers | Brenda Lee | 0.94 | energy 0.30, acoustic 0.65, tempo 97 bpm; fits genre |
| 3 | Those Good Old Dreams | Carpenters | 0.94 | energy 0.45, acoustic 0.66, tempo 92 bpm; fits genre |
| 4 | Walk On the Wild Side | Lou Reed | 0.94 | energy 0.32, acoustic 0.68, tempo 105 bpm; fits genre |
| 5 | Walk on By | Dionne Warwick | 0.94 | energy 0.33, acoustic 0.72, tempo 99 bpm; fits genre |

### 3. Mood mode: input `gym workout`

Detected mood: **workout** (target of roughly energy 0.90, acousticness 0.08, tempo 140 bpm).

| # | Song | Artist | Similarity | Why |
|---|---|---|---|---|
| 1 | We Built This City | Starship | 0.96 | energy 0.91, acoustic 0.05, tempo 144 bpm; fits genre |
| 2 | Stay Fly - Explicit Album Version | MJG, 8Ball, Three 6 Mafia, Young Buck | 0.96 | energy 0.88, acoustic 0.11, tempo 133 bpm; fits genre |
| 3 | Good Feeling | Flo Rida | 0.96 | energy 0.89, acoustic 0.06, tempo 128 bpm; fits genre |
| 4 | Some Like It Hot | The Power Station | 0.95 | energy 0.89, acoustic 0.09, tempo 126 bpm; fits genre |
| 5 | Rolex | Ayo & Teo | 0.95 | energy 0.89, acoustic 0.08, tempo 145 bpm; fits genre |

### 4. Unrecognized input: `xyz` in mood mode

The app does not guess. It shows a hint: *"I didn't recognize a mood in that. Try words like chill, cafe, study, gym, party, sad, happy, road trip."*

(Each song in the web app also appears with its album cover and a **▶ Preview** button, which plays a 10-second snippet.)

## Design Decisions

- **Content-based, not collaborative.** There is no listening history in the datasets, so closeness is computed from song attributes. This also makes every result explainable.
- **Metadata similarity for song mode.** Neither the Spotify CSV nor MusicOSet's metadata has audio features for song-to-song matching on every row, so song mode uses genre (weighted by rarity, so "vaporwave" counts more than "pop"), era, artist and popularity. *Trade-off:* it finds songs from the same scene and era, but not necessarily the same sound.
- **Audio features for mood mode.** Mood needs real signal (energy, acousticness, tempo), so I merged MusicOSet's `acoustic_features.csv`. *Trade-off:* only the ~20,400 MusicOSet songs have features, so the extra Spotify-top-1000 songs are left out of mood results.
- **Keyword matching instead of an LLM.** Mood words map to hand-written feature profiles. It is free, offline, deterministic and easy to debug. *Trade-off:* it only understands the ~14 moods I defined, and the profile numbers are my own estimates, not learned from data.
- **Diversity rule.** Without a cap, "Starboy" returned ten songs by The Weeknd, so results are limited to 2 per artist. *Trade-off:* a fan who wants more from one artist cannot get it.
- **Free, key-less APIs for extras.** Covers come from MusicOSet's `image_url` (~53% of songs) with Spotify oEmbed as a fallback; previews come from the iTunes Search API. Spotify removed its own preview URLs in 2024. *Trade-off:* the app needs internet, and a preview can be a different recording of the same song.
- **Matrix theme.** The linear-algebra look (bracketed cards, `sim = 0.82`, feature column vectors) fits the name and shows the "score a vector against a matrix" idea behind the ranking.

## Testing Summary

**Automated tests: 78 passing** (`pytest`, about 30 seconds)

| File | Tests | What it checks |
|---|---|---|
| `tests/test_recommender.py` | 2 | The original VibeMatch `Recommender` class |
| `tests/test_mood.py` | 28 | Mood keyword parsing (aliases, case, whole-word matching, no-match input), target blending, and ranking on a small hand-made catalog (chill vs. intense songs, songs without audio features are skipped, scores in 0-1, 2-per-artist cap, explanations present) |
| `tests/test_similar.py` | 26 | Song search (case, punctuation, blank input), recommendations on a small catalog (never returns the seed or its other versions, `k` respected, similar genre beats unrelated genre, "same era" labels), plus checks on the real ~21k-song catalog: no duplicates, valid feature ranges, 5 popular songs found and recommended, 40 random songs all obey the rules |
| `tests/test_mood_real_data.py` | 22 | All 14 moods return 10 valid results on the real data, and the results really sound right (workout mean energy > 0.75, sleep < 0.35, sad valence < 0.35, and so on), opposite moods return different songs, full sentences work, results are deterministic |

Manual runs on sample queries (*Starboy*, *Heat Waves*, *gym workout*, *sad rainy night*, *chill cafe*) also gave sensible, explainable lists.

**What didn't work at first (and the fix)**
- All 10 results were by the same artist, so I added the 2-per-artist cap.
- "Heat Waves (with iann dior)" was recommended for "Heat Waves", so I now strip `(with ...)` and `- Remastered` suffixes before comparing titles.
- Every mood result showed `sim = 1.00` because bonuses pushed raw scores above 1 and the display capped them. Scores are now scaled to 0-1 (typical values 0.94-0.96).
- "similar era" appeared for songs on the same album, so those now read "same era".
- Writing the tests exposed three more bugs, now fixed: one song had `tempo = 0` (missing data stored as zero), a perfect match could score `1.0000001` from float rounding, and searching "Seed-Song" did not find "Seed Song" because hyphens were deleted instead of becoming spaces.
- The old README command `python -m src.main` fails with an import error, so the setup steps use `python src/main.py`.

**Gaps and what I learned**
- **Gaps in the tests:** the Streamlit page itself (`app.py`), the cover lookup and the preview lookup call outside services and are not unit-tested; they were checked by hand. The mood tests check that results *fit the numbers*, not that a person would enjoy them, which still needs a human listening.
- **The catalog leans old.** MusicOSet is full of classic soft rock and soul, so mood results skew toward older songs. Dataset coverage shapes recommendations as much as the algorithm does.
- **Merging messy datasets is most of the work.** Only 156 of the Spotify top-1000 IDs overlapped with MusicOSet, and only ~55% of tracks had album art. Fallbacks (artist-name genre lookup, oEmbed covers) were needed.
- **Looking at real output catches bugs numbers hide.** The same-artist flood and the score saturation were only obvious when I read actual results.

## Reflection

This project taught me that a recommender is mostly decisions about data and definitions, not clever math. The ranking formula is a few lines; the hard parts were deciding what "close" means, what "chill" means in numbers, and what to do when the data is missing. Every one of those choices (weights, mood profiles, the artist cap) quietly shapes what users hear, which is why I made each result explain itself. It also showed me how an AI assistant fits into problem-solving: it is fast at building and iterating, but I still had to read the real outputs, notice what felt wrong, and decide what the system should value.

My graded responsible-AI reflection (how I collaborated with AI, a suggestion I accepted and one I rejected or revised, and the system's limitations) is in [`model_card.md`](model_card.md).
