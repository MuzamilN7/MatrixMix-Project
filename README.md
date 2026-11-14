# 🎵 MatrixMix

**Give it a song or describe a vibe, and it returns the 10 closest songs, with album covers, a short reason for each pick, and a 10-second preview. Built-in guardrails and an evaluation script check that the results can be trusted.**

## Original Project (Modules 1-3)

MatrixMix grew out of my **Music Recommender Simulation** (model name *VibeMatch 1.0*). That project was a small content-based recommender over a hand-made catalog of 18 songs (`data/songs.csv`). A user described a favorite mood, a favorite genre, and target levels for energy, valence, tempo, danceability and acousticness. Each song earned points for a mood match (3), a genre match (2), and numeric closeness to the targets, and the top 5 were returned with a plain-language explanation of the points. It still lives in `src/recommender.py` and `src/main.py`.

## Title and Summary

**MatrixMix** scales that idea up to real data, a real interface and a reliability layer. It merges two datasets into a catalog of about 21,000 songs and offers two ways to find music:

- **A song I like:** type a song, and get the 10 most similar songs.
- **A mood or vibe:** type something like *"a chill song to play in a cafe"*, and get songs whose audio features fit that mood.

**Why it matters:** recommenders decide what people hear, so it is useful to build one where every ranking can be explained *and checked*. Every result shows *why* it was picked (shared genres, same era, or the exact energy / acousticness / tempo that matched), and every list is verified against the system's own rules before it is shown.

### What's new compared to the original project

| New feature | Where | What it does |
|---|---|---|
| Real-data catalog | `src/similar.py` | Merges Spotify top-1000 + MusicOSet metadata + audio features into ~21,000 songs |
| Song-to-song recommender | `src/similar.py` | Finds the 10 closest songs by genre, artist, era and popularity |
| Mood search (specialized behavior) | `src/mood.py` | Turns plain-English requests into audio-feature targets (14 moods, aliases, blended moods) |
| Streamlit UI | `app.py`, `style.css` | Matrix-themed site with album covers and 10-second previews |
| **Guardrails** | `src/guardrails.py` | Input validation, an output self-check, a low-confidence warning, and an explicit-content filter |
| **Evaluation harness** | `evaluate.py` | Runs 43 checks on sample inputs through the real system and reports pass/fail |
| **Automated tests** | `tests/` | 113 pytest tests, including negative controls that prove the checks can fail |

## Architecture Overview

The full diagram is in [`diagram/system_diagram.mmd`](diagram/system_diagram.mmd) (Mermaid source). In short, data flows **input → guardrails → process → guardrails → output**, with human and automated checks around it:

1. **Input (Streamlit UI, `app.py`):** the user searches for a song or types a mood, and can turn the *Hide explicit songs* filter on or off (on by default).
2. **Input guardrail (`clean_query`):** the text is cleaned (control characters and extra spaces removed), rejected if empty or symbols-only, and shortened if longer than 100 characters.
3. **Data and catalog (`src/similar.py`):** three CSV sources are merged and de-duplicated into one catalog of ~21k songs, including MusicOSet's explicit flag.
4. **Process:**
   - *Retriever:* `search()` finds the song the user meant by title or artist.
   - *Song recommender:* scores every song against the seed by genre overlap (55%), era (20%), same artist (15%) and popularity (10%).
   - *Mood parser + recommender (`src/mood.py`):* turns keywords into target audio features, then ranks songs by closeness to that target.
   - *Rules:* at most 2 songs per artist, other versions of the seed song are hidden, and explicit songs are removed when the filter is on.
5. **Output guardrails (`verify_results`, `confidence`):** the list is self-checked (no duplicates, artist cap, scores in 0-1, sorted, explanations present, seed not repeated). If a rule is broken the list is **not shown**. If the matches are weak, a *low confidence* warning is shown.
6. **Output:** the top 10 songs, each with a similarity score and a "why" line, an album cover (MusicOSet image, falling back to Spotify oEmbed), and a 10-second preview (iTunes Search API).
7. **Human and testing checks:** the user listens to the preview and judges the match; the developer reads `evaluate.py` output and tunes weights and keywords; `pytest` and `evaluate.py` verify the code.

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
6. **Run the automated tests (about 40 seconds):**
   ```bash
   pytest
   ```
   Expected result: `113 passed`.
7. **Run the evaluation script (about 15 seconds):**
   ```bash
   python evaluate.py
   ```
   Expected result: `43/43 checks passed`. The script exits with code 1 if any check fails.
8. **(Optional) Run the original command-line recommender:**
   ```bash
   python src/main.py
   ```

Album covers and previews load from the internet, so you need a connection for those.

## Sample Interactions

These are real outputs from the system, with *Hide explicit songs* on (the default). In the web app each song also shows its album cover and a **▶ Preview** button that plays a 10-second snippet.

### 1. Song mode: input `Starboy` (The Weeknd, 2016)

```text
 1. Stargirl Interlude        The Weeknd      sim=0.98  same artist; shared genres: canadian contemporary r&b, canadian pop, pop; same era (2016)
 2. Die For You               The Weeknd      sim=0.98  same artist; shared genres: canadian contemporary r&b, canadian pop, pop; same era (2016)
 3. Scars To Your Beautiful   Alessia Cara    sim=0.60  shared genres: canadian contemporary r&b, pop; same era (2016)
 4. Here                      Alessia Cara    sim=0.59  shared genres: canadian contemporary r&b, pop; same era (2016)
 5. Love Yourself             Justin Bieber   sim=0.53  shared genres: canadian pop, pop; similar era (2015)
```

### 2. Mood mode: input `a chill song to play in a cafe`

Detected moods: `chill, cafe` (blended into a target of roughly energy 0.33, acousticness 0.65, tempo 92 bpm).

```text
 1. Make It with You          Bread            sim=0.94  energy 0.36, acoustic 0.66, tempo 84 bpm; fits genre
 2. Too Many Rivers           Brenda Lee       sim=0.94  energy 0.30, acoustic 0.65, tempo 97 bpm; fits genre
 3. Those Good Old Dreams     Carpenters       sim=0.94  energy 0.45, acoustic 0.66, tempo 92 bpm; fits genre
 4. Walk On the Wild Side     Lou Reed         sim=0.94  energy 0.32, acoustic 0.68, tempo 105 bpm; fits genre
 5. Walk on By                Dionne Warwick   sim=0.94  energy 0.33, acoustic 0.72, tempo 99 bpm; fits genre
```

### 3. Mood mode: input `gym workout`

Detected mood: `workout` (target of roughly energy 0.90, acousticness 0.08, tempo 140 bpm).

```text
 1. We Built This City        Starship            sim=0.96  energy 0.91, acoustic 0.05, tempo 144 bpm; fits genre
 2. Good Feeling              Flo Rida            sim=0.96  energy 0.89, acoustic 0.06, tempo 128 bpm; fits genre
 3. Some Like It Hot          The Power Station   sim=0.95  energy 0.89, acoustic 0.09, tempo 126 bpm; fits genre
 4. Rolex                     Ayo & Teo           sim=0.95  energy 0.89, acoustic 0.08, tempo 145 bpm; fits genre
 5. Rockstar                  Nickelback          sim=0.95  energy 0.91, acoustic 0.05, tempo 144 bpm; fits genre
```

Running each input twice gives the same list, so the system is consistent.

## Reliability and Guardrails

MatrixMix has four reliability mechanisms. Each one is shown below with an input, the behavior, and the result.

### 1. Input validation (`clean_query`)

| Input | Behavior | Result |
|---|---|---|
| `` (empty) or spaces only | Rejected before any search | Warning: *"Please type something to search for."* |
| `!!!???` | Rejected: no letters or digits | Warning: *"Please use letters or numbers in your search."* |
| `chill` + control characters + `cafe` | Control characters and extra spaces removed | Searches for `chill cafe` |
| 500 characters of text | Shortened to 100 characters | Info: *"Your text was longer than 100 characters, so I shortened it."* |
| `Señorita`, `Café del Mar`, `99 Problems` | Accents and numbers are valid | Accepted unchanged |

### 2. Unrecognized mood: say so instead of guessing

| Input | Behavior | Result |
|---|---|---|
| `xyz` (mood mode) | No mood keyword found, so no results are made up | Warning: *"I didn't recognize a mood in that. Try words like chill, cafe, study, gym, party, sad, happy, road trip."* |

### 3. Explicit-content filter ("Hide explicit songs", on by default)

The catalog carries MusicOSet's `explicit` flag (1,662 songs). Songs that exist only in the Spotify top-1000 list have no flag and are not filtered.

Input `gym workout`:

```text
Filter OFF -> includes explicit songs, for example:
   Stay Fly - Explicit Album Version   (MJG, 8Ball, Three 6 Mafia, Young Buck)
   The Show Goes On                    (Lupe Fiasco)
Filter ON  -> 0 explicit songs in the 10 results
```

### 4. Output self-check (`verify_results`) and low-confidence warning (`confidence`)

Before a list is shown, the app checks it against its own rules. If any rule fails, the list is **hidden** and an error explains why.

| Check | What a failure looks like | Behavior |
|---|---|---|
| No duplicates | The same song twice | List hidden |
| Artist cap | More than 2 songs by one artist | List hidden |
| Valid scores | A score outside 0-1, or results not sorted best-first | List hidden |
| Explanations | A result with an empty "why" | List hidden |
| Seed not repeated | A version of the song you searched for, such as `Heat Waves (with iann dior)` | List hidden |

When the lists are valid but the matches are weak, the app still shows them with a warning:

| Situation | Threshold | Message |
|---|---|---|
| Song mode, average score of the 10 results is low (seed has little genre/era data) | average < 0.45 | *"Low confidence: this song has little genre or era information, so these matches are rough guesses."* |
| Mood mode, even the best song fits poorly | best < 0.75 | *"Low confidence: no song fit that mood closely, so these are the nearest options."* |

In normal use these thresholds are rarely reached (typical mood results score 0.85-0.96), so a warning means something unusual is happening.

### The evaluation script

`python evaluate.py` runs the real system on a fixed set of inputs and prints a pass/fail report. It covers six popular songs in song mode, eight mood requests, and the guardrail cases above. Example output (shortened):

```text
Loading catalog...
Catalog: 21,167 songs

== Song mode ==
  [PASS] 'Starboy': 10 results obey all rules  (10 results)
  [PASS] 'Starboy': results share a genre with the seed  (100% share a genre)
  [PASS] 'Starboy': same answer on a second run
  ...

== Mood mode ==
  [PASS] 'gym workout': mean energy > 0.75  (moods=['workout'], mean energy=0.90)
  [PASS] 'sleep': mean energy < 0.35  (moods=['sleep'], mean energy=0.16)
  [PASS] 'I want a chill song to play in a cafe': mean acousticness > 0.4  (moods=['chill', 'cafe'], mean acousticness=0.68)
  [PASS] 'sad rainy night': mean valence < 0.35  (moods=['sad'], mean valence=0.20)
  ...

== Guardrails ==
  [PASS] input '' is rejected  (Please type something to search for.)
  [PASS] input '!!!???' is rejected  (Please use letters or numbers in your search.)
  [PASS] input 'chill\x00\x07 cafe' is cleaned  (-> 'chill cafe')
  [PASS] input 'aaaaaaaaaa...(500 chars)' is truncated with a warning  (-> 100 chars, warnings=1)
  [PASS] unrecognized mood returns nothing, not a guess
  [PASS] 'clean only' never returns an explicit song (all 14 moods)  (0 explicit songs)
  [PASS] self-check catches a bad list  (duplicate + unsorted list was flagged)
  [PASS] low-confidence warning fires on weak matches

43/43 checks passed in 14.9s
```

## Design Decisions

- **Content-based, not collaborative.** There is no listening history in the datasets, so closeness is computed from song attributes. This also makes every result explainable.
- **Metadata similarity for song mode.** Neither the Spotify CSV nor MusicOSet's metadata has audio features for song-to-song matching on every row, so song mode uses genre (weighted by rarity, so "vaporwave" counts more than "pop"), era, artist and popularity. *Trade-off:* it finds songs from the same scene and era, but not necessarily the same sound.
- **Audio features for mood mode.** Mood needs real signal (energy, acousticness, tempo), so I merged MusicOSet's `acoustic_features.csv`. *Trade-off:* only the ~20,400 MusicOSet songs have features, so the extra Spotify-top-1000 songs are left out of mood results.
- **Keyword matching instead of an LLM.** Mood words map to hand-written feature profiles. It is free, offline, deterministic and easy to test. An LLM would understand any phrasing but needs a paid API key, and a public app could run up a bill. *Trade-off:* it only understands the ~14 moods I defined, and the profile numbers are my own estimates, not learned from data.
- **Rule-based guardrails instead of a second model.** The self-check and filters are plain code, so they are fast, free and predictable. *Trade-off:* they catch broken lists and explicit songs, but cannot judge whether a song "feels" right. That still needs a human listening.
- **Filter on by default.** Explicit songs are hidden unless the user turns the filter off, because recommendations for a cafe or a shared space should be safe by default. *Trade-off:* songs only in the Spotify top-1000 list have no flag, so they are not filtered.
- **Hide a broken list instead of showing it.** If the self-check fails, showing nothing and explaining why is better than showing wrong results confidently.
- **Diversity rule.** Without a cap, "Starboy" returned ten songs by The Weeknd, so results are limited to 2 per artist. *Trade-off:* a fan who wants more from one artist cannot get it.
- **Free, key-less APIs for extras.** Covers come from MusicOSet's `image_url` (~53% of songs) with Spotify oEmbed as a fallback; previews come from the iTunes Search API. Spotify removed its own preview URLs in 2024. *Trade-off:* the app needs internet, and a preview can be a different recording of the same song.
- **Matrix theme.** The linear-algebra look (bracketed cards, `sim = 0.82`, feature column vectors) fits the name and shows the "score a vector against a matrix" idea behind the ranking.

## Testing Summary

**Automated tests: 113 passing** (`pytest`, about 40 seconds) and **43/43 evaluation checks** (`python evaluate.py`).

| File | Tests | What it checks |
|---|---|---|
| `tests/test_recommender.py` | 2 | The original VibeMatch `Recommender` class |
| `tests/test_mood.py` | 28 | Mood keyword parsing (aliases, case, whole-word matching, no-match input), target blending, and ranking on a small hand-made catalog |
| `tests/test_similar.py` | 26 | Song search (case, punctuation, blank input), recommendations on a small catalog (never returns the seed or its other versions, `k` respected, similar genre beats unrelated genre, "same era" labels), plus checks on the real ~21k-song catalog |
| `tests/test_mood_real_data.py` | 22 | All 14 moods return 10 valid results on the real data, and the results really sound right (workout mean energy > 0.75, sleep < 0.35, and so on), results are deterministic |
| `tests/test_guardrails.py` | 35 | Input validation, every self-check rule (each one is shown to *fail* on a deliberately bad list), the low-confidence warning, and the explicit filter, with negative controls proving explicit songs do appear when the filter is off |

The app itself was also driven end to end with Streamlit's test harness: a normal mood request, a normal song request, symbols-only input, blank-ish input, an unrecognized mood and a 300-character input all ran with no errors and showed the right message.

**What didn't work at first (and the fix)**
- All 10 results were by the same artist, so I added the 2-per-artist cap.
- "Heat Waves (with iann dior)" was recommended for "Heat Waves", so I now strip `(with ...)` and `- Remastered` suffixes before comparing titles, and the self-check also watches for this.
- Every mood result showed `sim = 1.00` because bonuses pushed raw scores above 1 and the display capped them. Scores are now scaled to 0-1 (typical values 0.94-0.96).
- "similar era" appeared for songs on the same album, so those now read "same era".
- Writing the tests exposed three more bugs, now fixed: one song had `tempo = 0` (missing data stored as zero), a perfect match could score `1.0000001` from float rounding, and searching "Seed-Song" did not find "Seed Song" because hyphens were deleted instead of becoming spaces.
- A "gym workout" result included an explicit song, which led to carrying the `explicit` flag into the catalog and adding the filter.
- The old README command `python -m src.main` fails with an import error, so the setup steps use `python src/main.py`.

**Gaps and what I learned**
- **The tests check numbers, not taste.** They prove that "workout" results have high energy, not that a person would enjoy them. That still needs a human listening, which is why the previews are in the app.
- **Outside services are not unit-tested.** The cover and preview lookups call Spotify and iTunes, so they were checked by hand.
- **The catalog leans old.** MusicOSet is full of classic soft rock and soul, so mood results skew toward older songs. Dataset coverage shapes recommendations as much as the algorithm does.
- **Merging messy datasets is most of the work.** Only 156 of the Spotify top-1000 IDs overlapped with MusicOSet, and only ~55% of tracks had album art. Fallbacks (artist-name genre lookup, oEmbed covers) were needed.
- **Looking at real output catches bugs numbers hide.** The same-artist flood and the score saturation were only obvious when I read actual results.

## Reflection

This project taught me that a recommender is mostly decisions about data and definitions, not clever math. The ranking formula is a few lines; the hard parts were deciding what "close" means, what "chill" means in numbers, and what to do when the data is missing. Every one of those choices (weights, mood profiles, the artist cap) quietly shapes what users hear, which is why I made each result explain itself, and why I added guardrails that can refuse to show a list. It also showed me how an AI assistant fits into problem-solving: it is fast at building and iterating, but I still had to read the real outputs, notice what felt wrong, and decide what the system should value.

My graded responsible-AI reflection (limitations and biases, misuse, what surprised me in testing, and how I collaborated with AI, including a suggestion I accepted and one I rejected or revised) is in [`model_card.md`](model_card.md).
