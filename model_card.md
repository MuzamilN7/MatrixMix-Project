# 🎧 Model Card: Music Recommender Simulation

> **Which part to read:** this model card began as the Module 1-3 card for **VibeMatch 1.0** (sections 1-9 below, kept for the record). The current project, **MatrixMix**, is documented in the **"MatrixMix: Responsible-AI Reflection"** part starting at section 10: limitations and biases, misuse and prevention, what surprised me while testing, how I worked with AI (one suggestion accepted, one revised), and what I would do next.


## 1. Model Name  

**VibeMatch 1.0**

---

## 2. Goal and Intended Use  

**Goal:** The recommender suggests songs a user might like. It picks the top 5 songs from a small catalog. It also tells the user why each song was picked.

**What it assumes about the user:** The user can name a favorite mood and genre. The user can also say how high or low they want things like energy and tempo. It assumes these tastes do not change.

**Intended use:**

- Classroom learning about how recommenders work.
- Testing simple scoring ideas on a small, safe dataset.
- Showing how point rules turn into a ranked list.

**Not intended for:**

- Real music apps or real users. The catalog is far too small.
- Judging a person's taste or deciding what they "should" like.
- Any decision that matters. It has no checks for bad input.
- Fair exposure for artists. It does not try to be fair to them.

---

## 3. How the Model Works  

The recommender is a points game. Every song gets a score. The best scores win.

**What it looks at in a song:** mood, genre, and five numbers. The numbers are energy, valence (how upbeat), tempo, danceability and acousticness.

**What you tell it:** your favorite mood and genre. Also how high or low you want each number. You can skip any of them.

**How a song earns points:**

- **Mood match: 3 points.** All or nothing.
- **Genre match: 2 points.** All or nothing.
- **Energy: up to 1.5 points.** The closer to your number, the more points.
- **Valence, tempo, danceability, acousticness: up to 0.5 points each.** Same idea, but worth less.

The most a song can score is 8.5. The songs are sorted from high to low. The top 5 are shown with reasons, like "Mood match (+3)".

**Key idea:** closer is better, not higher is better. If you ask for calm music (energy 0.3), a song at 0.9 loses points. So does a song at 0.0.

**What I built:** the starter had empty placeholders. I wrote the song loader, the scorer and the ranker.

---

## 4. Data  

The catalog is one file: `data/songs.csv`. It has **18 songs**.

Each song has:

- A title and an artist.
- A genre and a mood.
- Five numbers: energy, valence, tempo, danceability and acousticness.

**What is in it:**

- 15 genres. Lofi has 3 songs, pop has 2, and the other 13 have 1 each.
- 14 moods. Chill has 3 songs, happy and intense have 2 each, and the rest have 1.
- Energy runs from 0.21 to 0.97. Tempo runs from 60 to 168 bpm.
- Nine songs have energy above 0.7. Only four sit in the middle.

**Limits:**

- It is tiny. Real apps have millions of songs.
- Most genres have just one song.
- Many tastes are missing, such as K-pop, Latin pop, gospel and world music.
- It has no play counts, no history and no user ratings.

---

## 5. Strengths  

The system works best when the user's mood and genre are in the catalog.

- **Clear reasons.** Every song shows how it earned its points. This makes the results easy to check.
- **Good match for clear tastes.** The classical and melancholy profile got Moonlit Sonata first. This is what I expected.
- **Calm and quiet tastes work.** The low-energy, acoustic profile got Moonlit Sonata, Harbor Lights and Spacewalk Thoughts. All three are quiet songs.
- **"Closer is better" works.** A user who asks for calm music is not shown loud songs just because they have higher numbers.
- **Normal starter profile looks right.** Pop and happy put Sunrise City first. Rooftop Lights, another happy song, came second.

---

## 6. Limitations and Bias 

Where the system struggles or behaves unfairly. 

Prompts:  

- Features it does not consider  
- Genres or moods that are underrepresented  
- Cases where the system overfits to one preference  
- Ways the scoring might unintentionally favor some users  

**Weakness found in testing: one-song genres leave most of the top 5 as filler.**

- Mood and genre matches are worth up to 5 points. All the numbers together are worth only 3.5.
- 13 of the 15 genres have just one song.
- Take the "melancholy classical, energy 0.95" profile. Moonlit Sonata is the only classical song. It scores 5.89.
- The other four slots go to loud songs like Gym Hero and Iron Requiem. They score about 1.5 each. They only match on energy.
- There is no minimum score. There is no idea of related genres or moods.
- So a user with a niche taste gets one real match, then filler.

---

## 7. Evaluation  

How you checked whether the recommender behaved as expected. 

Prompts:  

- Which user profiles you tested  
- What you looked for in the recommendations  
- What surprised you  
- Any simple tests or comparisons you ran  

No need for numeric metrics unless you created some.

### Profiles tested

I ran the starter profile (pop, happy, energy 0.8) and 15 deliberately awkward "edge case" profiles through the recommender, and looked at the top 5 songs and the reasons for each score:

| # | Profile | What it tests |
|---|---------|---------------|
| Start | pop, happy, energy 0.8 | The normal case |
| 1 | classical, melancholy, energy 0.95, acousticness 0.97 | Tastes that contradict each other |
| 2 | metal, happy, energy 0.97 | Mood and genre pointing at different songs |
| 3 | vaporwave, serene, energy 0.5 | Genre and mood that are not in the catalog |
| 4 | nothing at all | An empty profile |
| 5 | "Pop", " happy", energy 0.8 | Capital letter and stray space |
| 6 | pop, happy, energy 5.0 | A number outside the 0 to 1 range |
| 7 | energy -1 | A negative number |
| 8 | tempo 0.5 | Tempo given on the wrong scale |
| 9 | tempo 300 bpm | A tempo faster than any song |
| 10 | every number set to the middle | No genre or mood, only numbers |
| 11, 12 | energy as the text "0.8", energy left as None | Wrong kinds of values |
| 13 | mood given as a list | Wrong kind of value for mood |
| 14 | misspelled setting names | A profile the recommender cannot read |
| 15 | energy 0, acousticness 1, valence 0 | Extreme quiet, sad, acoustic taste |

### Why "Gym Hero" keeps showing up for people who just want "Happy Pop"

Gym Hero is a pop song. But its mood is "intense", not happy.

For the starter profile it came third with 3.30 points. It got 2 points for being pop. It got 1.30 for having a close energy (0.93 vs 0.8). It got 0 for mood.

The catalog has only two pop songs. After Sunrise City, Gym Hero is the only other pop song. The system cannot tell that "intense" feels different from "happy". It only checks if the words match.

In my weight test, Gym Hero even jumped above Rooftop Lights, a real happy song.

### Comparing pairs of profiles

- **Starter (pop/happy) vs. 2 (metal/happy):** Sunrise City is first for both. The metal fan gets Iron Requiem third. It is the only metal song. Mood is worth more than genre, so the metal fan's favorite genre only comes third.
- **Starter vs. 5 ("Pop", " happy"):** Only a capital letter and a space changed. The top score fell from 6.47 to 1.47. "Pop" is not "pop" to the computer. A person would see the same profile. This is a real flaw.
- **Starter (energy 0.8) vs. 6 (energy 5.0):** At 0.8, energy helps rank the songs. At 5.0, every song gets zero energy points. The system quietly ignores that preference.
- **1 (sad classical, high energy) vs. 15 (quiet, acoustic):** Both get Moonlit Sonata first. User 15 then gets calm songs, which fits. User 1 asked for loud and acoustic. No song is both. So the rest are loud songs like Gym Hero. That makes sense in the math, but a classical fan would not want them.
- **3 (unknown genre) vs. 10 (all numbers in the middle):** Neither matches a genre or mood. Both are ranked on numbers only. Profile 10 uses five numbers, so scores are about 3 instead of 1.5. The same average songs win both. Average songs win when the user has no strong taste.
- **7 (energy -1) vs. 9 (tempo 300):** Every song scores 0.00 in both. Both lists are just the first five rows of the file. They look like real picks, but they are not.
- **8 (tempo 0.5) vs. 9 (tempo 300):** Tempo 0.5 is near the slowest song, so slow songs get small scores. Tempo 300 is beyond every song, so all scores are zero. The system cannot tell when a number looks wrong.
- **4 (empty), 13 (mood as list), 14 (misspelled keys):** All three give 0.00 for every song and the same five songs. To the system, they all mean "I understood nothing."
- **11 (energy as text) vs. 12 (energy as None):** Both crash. These are the only profiles that fail outright.

### What surprised me

- **A one-letter slip erased the whole profile.** I expected "Pop" to still work. Instead the user lost 5 points of match on every song.
- **Zero scores still produce a list.** Four different kinds of bad input all gave a confident-looking top 5 made entirely of the first songs in the file.
- **The mood bonus overpowers everything.** The happy-metal user was shown two happy songs before the only metal song, even though that metal song's energy was nearly exact.
- **Almost every song is reachable.** I tried 1,000s of combinations of genre, mood and energy, and every song in the catalog showed up at least once. Some appeared much more than others (Spacewalk Thoughts 491 times, Iron Requiem 149), so no song is invisible, but the loud, electric songs get chosen least.

---

## 8. Future Work  

1. **Clean up the input.** Ignore capital letters and extra spaces. Warn the user about bad numbers and unknown settings. Do not crash.
2. **Count similar moods and genres.** Give partial points for pairs like pop and indie pop, or chill and relaxed. Right now only an exact word match counts.
3. **Show fewer, better results.** Add a minimum score. Do not list songs that only match on one number. Also avoid five songs from the same artist or genre.
4. **Add more songs.** Most genres have only one song. A bigger catalog would fix many of the problems I found.

---

## 9. Personal Reflection  

**Biggest learning moment.** I thought the hard part would be the math. It was not. The hard part was deciding what the weights mean. When I halved the mood points and doubled the energy points, one profile got better and another got worse. That showed me that every weight is a choice about what matters.

**How AI helped, and when I double-checked.** AI helped me build the scoring code. It also helped me think of the edge-case profiles, like a capital letter in the genre or an energy of 5.0. I did not trust its explanations by themselves. I ran the profiles and read the real scores. That is how I confirmed that "Pop" scored differently from "pop". Every claim about why a song ranked where it did should be checked against the actual numbers.

**What surprised me.** Simple point rules still feel like real recommendations. The list has reasons and it usually looks sensible. But when the profile was empty or the numbers were bad, it still gave a confident top 5. Those songs were just the first rows of the file. A recommendation can look smart even when the system understood nothing.

**What I would try next.** I would add partial credit for similar moods and genres. I would stop the system from listing songs with a score of zero. I would also add more songs, so that each genre has several choices. Then I would test it again with the same profiles and see what changed.

**How this changed my view of music apps.** A "for you" list is the result of many small choices about weights and data. If the data is lopsided, the list will be lopsided too.And the amount of songs and data needed is insurmountable



========================================================
PROFILE 1 conflicting (sad classical but energy 0.95)
{'genre': 'classical', 'mood': 'melancholy', 'energy': 0.95, 'acousticness': 0.97}
========================================================

#1  Moonlit Sonata  (Elara Quill)  [classical/melancholy]
    Score: 5.89
      - Mood match (+3)
      - Genre match (+2)
      - Energy closeness (+0.39)
      - Acousticness closeness (+0.50)

#2  Gym Hero  (Max Pulse)  [pop/intense]
    Score: 1.51
      - Energy closeness (+1.47)
      - Acousticness closeness (+0.04)

#3  Storm Runner  (Voltline)  [rock/intense]
    Score: 1.51
      - Energy closeness (+1.44)
      - Acousticness closeness (+0.07)

#4  Iron Requiem  (Cinder Throne)  [metal/angry]
    Score: 1.50
      - Energy closeness (+1.47)
      - Acousticness closeness (+0.04)

#5  Afterglow Static  (Pale Circuit)  [electronic/euphoric]
    Score: 1.46
      - Energy closeness (+1.41)
      - Acousticness closeness (+0.05)

========================================================
PROFILE 2 mood vs genre (happy+metal)
{'genre': 'metal', 'mood': 'happy', 'energy': 0.97}
========================================================

#1  Sunrise City  (Neon Echo)  [pop/happy]
    Score: 4.28
      - Mood match (+3)
      - Energy closeness (+1.27)

#2  Rooftop Lights  (Indigo Parade)  [indie pop/happy]
    Score: 4.19
      - Mood match (+3)
      - Energy closeness (+1.19)

#3  Iron Requiem  (Cinder Throne)  [metal/angry]
    Score: 3.50
      - Genre match (+2)
      - Energy closeness (+1.50)

#4  Gym Hero  (Max Pulse)  [pop/intense]
    Score: 1.44
      - Energy closeness (+1.44)

#5  Storm Runner  (Voltline)  [rock/intense]
    Score: 1.41
      - Energy closeness (+1.41)

========================================================
PROFILE 3 unknown genre/mood
{'genre': 'vaporwave', 'mood': 'serene', 'energy': 0.5}
========================================================

#1  Dust Road Home  (Hollow Pines)  [country/nostalgic]
    Score: 1.47
      - Energy closeness (+1.47)

#2  Velvet Hour  (Marisol Vane)  [r&b/romantic]
    Score: 1.47
      - Energy closeness (+1.47)

#3  Midnight Coding  (LoRoom)  [lofi/chill]
    Score: 1.38
      - Energy closeness (+1.38)

#4  Focus Flow  (LoRoom)  [lofi/focused]
    Score: 1.35
      - Energy closeness (+1.35)

#5  Coffee Shop Stories  (Slow Stereo)  [jazz/relaxed]
    Score: 1.30
      - Energy closeness (+1.30)

========================================================
PROFILE 4 empty prefs
{}
========================================================

#1  Sunrise City  (Neon Echo)  [pop/happy]
    Score: 0.00
      - 

#2  Midnight Coding  (LoRoom)  [lofi/chill]
    Score: 0.00
      - 

#3  Storm Runner  (Voltline)  [rock/intense]
    Score: 0.00
      - 

#4  Library Rain  (Paper Lanterns)  [lofi/chill]
    Score: 0.00
      - 

#5  Gym Hero  (Max Pulse)  [pop/intense]
    Score: 0.00
      - 

========================================================
PROFILE 5 case/whitespace
{'genre': 'Pop', 'mood': ' happy', 'energy': 0.8}
========================================================

#1  Sunrise City  (Neon Echo)  [pop/happy]
    Score: 1.47
      - Energy closeness (+1.47)

#2  Bassline Cathedral  (Kilo Vandal)  [hip hop/confident]
    Score: 1.47
      - Energy closeness (+1.47)

#3  Rooftop Lights  (Indigo Parade)  [indie pop/happy]
    Score: 1.44
      - Energy closeness (+1.44)

#4  Carnival Pulse  (Sol y Fuego)  [reggaeton/playful]
    Score: 1.43
      - Energy closeness (+1.43)

#5  Night Drive Loop  (Neon Echo)  [synthwave/moody]
    Score: 1.42
      - Energy closeness (+1.42)

========================================================
PROFILE 6 out-of-range energy 5.0
{'genre': 'pop', 'mood': 'happy', 'energy': 5.0}
========================================================

#1  Sunrise City  (Neon Echo)  [pop/happy]
    Score: 5.00
      - Mood match (+3)
      - Genre match (+2)
      - Energy closeness (+0.00)

#2  Rooftop Lights  (Indigo Parade)  [indie pop/happy]
    Score: 3.00
      - Mood match (+3)
      - Energy closeness (+0.00)

#3  Gym Hero  (Max Pulse)  [pop/intense]
    Score: 2.00
      - Genre match (+2)
      - Energy closeness (+0.00)

#4  Midnight Coding  (LoRoom)  [lofi/chill]
    Score: 0.00
      - Energy closeness (+0.00)

#5  Storm Runner  (Voltline)  [rock/intense]
    Score: 0.00
      - Energy closeness (+0.00)

========================================================
PROFILE 7 negative energy -1
{'energy': -1.0}
========================================================

#1  Sunrise City  (Neon Echo)  [pop/happy]
    Score: 0.00
      - Energy closeness (+0.00)

#2  Midnight Coding  (LoRoom)  [lofi/chill]
    Score: 0.00
      - Energy closeness (+0.00)

#3  Storm Runner  (Voltline)  [rock/intense]
    Score: 0.00
      - Energy closeness (+0.00)

#4  Library Rain  (Paper Lanterns)  [lofi/chill]
    Score: 0.00
      - Energy closeness (+0.00)

#5  Gym Hero  (Max Pulse)  [pop/intense]
    Score: 0.00
      - Energy closeness (+0.00)

========================================================
PROFILE 8 tempo 0.5
{'tempo_bpm': 0.5}
========================================================

#1  Spacewalk Thoughts  (Orbit Bloom)  [ambient/chill]
    Score: 0.22
      - Tempo closeness (+0.22)

#2  Moonlit Sonata  (Elara Quill)  [classical/melancholy]
    Score: 0.20
      - Tempo closeness (+0.20)

#3  Library Rain  (Paper Lanterns)  [lofi/chill]
    Score: 0.17
      - Tempo closeness (+0.17)

#4  Midnight Coding  (LoRoom)  [lofi/chill]
    Score: 0.14
      - Tempo closeness (+0.14)

#5  Focus Flow  (LoRoom)  [lofi/focused]
    Score: 0.13
      - Tempo closeness (+0.13)

========================================================
PROFILE 9 tempo 300 bpm
{'tempo_bpm': 300}
========================================================

#1  Sunrise City  (Neon Echo)  [pop/happy]
    Score: 0.00
      - Tempo closeness (+0.00)

#2  Midnight Coding  (LoRoom)  [lofi/chill]
    Score: 0.00
      - Tempo closeness (+0.00)

#3  Storm Runner  (Voltline)  [rock/intense]
    Score: 0.00
      - Tempo closeness (+0.00)

#4  Library Rain  (Paper Lanterns)  [lofi/chill]
    Score: 0.00
      - Tempo closeness (+0.00)

#5  Gym Hero  (Max Pulse)  [pop/intense]
    Score: 0.00
      - Tempo closeness (+0.00)

========================================================
PROFILE 10 all-numeric midpoint
{'energy': 0.5, 'valence': 0.5, 'tempo_bpm': 114, 'danceability': 0.5, 'acousticness': 0.5}
========================================================

#1  Dust Road Home  (Hollow Pines)  [country/nostalgic]
    Score: 3.14
      - Energy closeness (+1.47)
      - Valence closeness (+0.44)
      - Tempo closeness (+0.42)
      - Danceability closeness (+0.47)
      - Acousticness closeness (+0.34)

#2  Velvet Hour  (Marisol Vane)  [r&b/romantic]
    Score: 3.05
      - Energy closeness (+1.47)
      - Valence closeness (+0.40)
      - Tempo closeness (+0.36)
      - Danceability closeness (+0.38)
      - Acousticness closeness (+0.44)

#3  Midnight Coding  (LoRoom)  [lofi/chill]
    Score: 3.02
      - Energy closeness (+1.38)
      - Valence closeness (+0.47)
      - Tempo closeness (+0.33)
      - Danceability closeness (+0.44)
      - Acousticness closeness (+0.40)

#4  Focus Flow  (LoRoom)  [lofi/focused]
    Score: 2.96
      - Energy closeness (+1.35)
      - Valence closeness (+0.46)
      - Tempo closeness (+0.34)
      - Danceability closeness (+0.45)
      - Acousticness closeness (+0.36)

#5  Harbor Lights  (Salt & Cedar)  [folk/wistful]
    Score: 2.89
      - Energy closeness (+1.25)
      - Valence closeness (+0.47)
      - Tempo closeness (+0.38)
      - Danceability closeness (+0.49)
      - Acousticness closeness (+0.30)

========================================================
PROFILE 11 energy as string
{'energy': '0.8'}
========================================================

  CRASH: TypeError: unsupported operand type(s) for -: 'float' and 'str'

========================================================
PROFILE 12 None value
{'energy': None}
========================================================

  CRASH: TypeError: unsupported operand type(s) for -: 'float' and 'NoneType'

========================================================
PROFILE 13 mood as list
{'mood': ['happy', 'chill']}
========================================================

#1  Sunrise City  (Neon Echo)  [pop/happy]
    Score: 0.00
      - 

#2  Midnight Coding  (LoRoom)  [lofi/chill]
    Score: 0.00
      - 

#3  Storm Runner  (Voltline)  [rock/intense]
    Score: 0.00
      - 

#4  Library Rain  (Paper Lanterns)  [lofi/chill]
    Score: 0.00
      - 

#5  Gym Hero  (Max Pulse)  [pop/intense]
    Score: 0.00
      - 

========================================================
PROFILE 14 typo keys
{'favorite_genre': 'pop', 'target_energy': 0.8}
========================================================

#1  Sunrise City  (Neon Echo)  [pop/happy]
    Score: 0.00
      - 

#2  Midnight Coding  (LoRoom)  [lofi/chill]
    Score: 0.00
      - 

#3  Storm Runner  (Voltline)  [rock/intense]
    Score: 0.00
      - 

#4  Library Rain  (Paper Lanterns)  [lofi/chill]
    Score: 0.00
      - 

#5  Gym Hero  (Max Pulse)  [pop/intense]
    Score: 0.00
      - 

========================================================
PROFILE 15 extreme low energy+acoustic
{'energy': 0.0, 'acousticness': 1.0, 'valence': 0.0}
========================================================

#1  Moonlit Sonata  (Elara Quill)  [classical/melancholy]
    Score: 2.04
      - Energy closeness (+1.19)
      - Valence closeness (+0.38)
      - Acousticness closeness (+0.48)

#2  Harbor Lights  (Salt & Cedar)  [folk/wistful]
    Score: 1.73
      - Energy closeness (+1.00)
      - Valence closeness (+0.28)
      - Acousticness closeness (+0.45)

#3  Spacewalk Thoughts  (Orbit Bloom)  [ambient/chill]
    Score: 1.72
      - Energy closeness (+1.08)
      - Valence closeness (+0.17)
      - Acousticness closeness (+0.46)

#4  Library Rain  (Paper Lanterns)  [lofi/chill]
    Score: 1.60
      - Energy closeness (+0.98)
      - Valence closeness (+0.20)
      - Acousticness closeness (+0.43)

#5  Coffee Shop Stories  (Slow Stereo)  [jazz/relaxed]
    Score: 1.54
      - Energy closeness (+0.95)
      - Valence closeness (+0.15)
      - Acousticness closeness (+0.45)

---

# MatrixMix: Responsible-AI Reflection

*Sections 1-9 above document the original VibeMatch 1.0 (Modules 1-3). This part covers MatrixMix, the scaled-up version that uses about 21,000 real songs, a mood search, album covers and previews.*

## 10. Limitations and Biases in MatrixMix

**The data decides what gets recommended, and it is skewed.**
- **Old music is over-represented.** The median song in the catalog is from 2006, and about 18% are from before 1990. Mood results lean toward classic soft rock and soul. "A chill song for a cafe" returns Bread, Brenda Lee and the Carpenters, not anything recent. A user who wants modern music gets worse results without any warning.
- **Not every song can be found by every route.** Only about 96% of songs have audio features, so the Spotify-top-1000 songs that are not in MusicOSet can never appear in mood results. About 11% of songs have no genre at all, so song-to-song matching for them leans only on era, popularity and artist.
- **Odd artists are everywhere.** The most common "artists" in the catalog are The Karaoke Channel (110 songs) and Glee Cast (91). A song-to-song match can surface a karaoke cover that is "similar" on paper but is not what a listener wants.
- **Genres belong to artists, not songs.** Every song inherits all of its artist's genres. A ballad by a rock band is treated as rock, and a band that changed style is stuck with every label.
- **Popularity and fame create a rich-get-richer effect.** The score gives popularity 10% of the weight in song mode and a small tie-break in mood mode. Famous artists get recommended more, and lesser-known artists get fewer chances.
- **Similarity is only metadata.** Song mode compares genre, artist, era and popularity, not how the song sounds, so it can match songs from the same scene that sound nothing alike.

**The mood system is hand-written and narrow.**
- In keyword mode only 14 moods are understood. Anything else ("nostalgic", "lonely road at 3am") returns nothing instead of a best guess. The optional Groq AI parser removes that limit, but it brings its own problems (see "The AI parser" below).
- The numbers in each mood profile (for example "chill = energy 0.30, acousticness 0.60") are my own estimates, not learned from listeners. They reflect one person's idea of what "chill" or "workout" sounds like, and other cultures or tastes may disagree.
- Keywords like "love", "date" and "dinner" all map to "romantic", and "car" or "drive" map to "road trip", which will sometimes fire on words that are not really about mood.

**The AI parser (Groq LLM) has its own limitations.**
- **It reflects the model's idea of a mood.** When the LLM decides what "cozy bookshop" means in numbers, it uses patterns from its training data. Those can encode cultural assumptions about what music "belongs" to a mood or a place, and I cannot inspect them.
- **It is not deterministic or always available.** The same sentence can produce slightly different numbers on different days, the free tier has rate limits, and the call can time out. That is why keyword matching stays as a fallback and results are cached.
- **A confident wrong answer looks the same as a right one.** The validation step guarantees the numbers are well-formed and in range. It cannot tell whether "falling asleep" was mapped to the *right* energy. I check this with evaluation cases (for example "sleep" should be low energy), but only a few phrasings are covered.
- **Only a few phrasings were tested live.** Most of the AI path is tested with a fake client. With a real key I ran three requests (a bookshop, a marathon, falling asleep) and one gibberish input against Groq, and all passed, including Groq accepting my strict JSON schema. Other phrasings, languages and odd inputs are untested, so the model could still map something to unexpected numbers.
- **Privacy:** the user's typed text is sent to an outside company when the AI parser is on. On a free tier, the provider's terms may allow it to use prompts to improve its products, so users should not type personal information.

**Missing content signals.**
- The system does not understand lyrics or language. It also found explicit songs at first: a "gym workout" result included "Stay Fly - Explicit Album Version". I fixed this by carrying MusicOSet's `explicit` flag into the catalog and adding a "Hide explicit songs" filter that is on by default. The remaining gap is that the flag only exists for MusicOSet songs, so songs that appear only in the Spotify top-1000 list are never filtered, and the flag cannot catch clean-labeled songs with mature themes.
- Covers and previews depend on outside services. About 47% of covers come from a fallback lookup, and a preview can be a different recording of the same song or can be missing.

## 11. Could the AI Be Misused, and How Would I Prevent It?

MatrixMix is low-stakes. It suggests songs, it makes no decisions about people, and it stores nothing about users. Even so, I can see a few ways it could cause harm.

- **Playing inappropriate content in public.** Someone could use mood search to build a playlist for a cafe, a classroom or a kids' event and get explicit songs. *Prevention (done):* the catalog now carries the dataset's `explicit` flag, and a "Hide explicit songs" filter is on by default. An evaluation check confirms that none of the 14 moods return an explicit song with the filter on, and a negative control confirms explicit songs do appear with it off.
- **Showing broken or low-quality results with confidence.** A bug could make the app show duplicates, too many songs by one artist, or weak matches as if they were good. *Prevention (done):* every list is self-checked before it is shown and is hidden with an explanation if a rule fails, and weak matches get a "low confidence" warning. Typed input is validated and cleaned so that empty, symbols-only or very long text cannot reach the search.
- **Skewing what people hear.** If a real service used this, the popularity bonus and the old-music bias would steer listeners toward famous and older artists and make it harder for new or small artists to be discovered. *Prevention:* cap the popularity weight, add a "discover newer / lesser-known" option, and keep the 2-songs-per-artist rule, which already spreads results out.
- **Overtrusting the "match" percentage.** A score like `sim = 0.94` looks precise, but it only measures closeness on a few numbers. I made every result show a plain-language reason so that users can see what the score means and disagree with it.
- **Scraping or hammering the free services.** The app calls the Spotify oEmbed and iTunes endpoints. Results are cached and calls happen only when a user clicks a preview or a cover is missing, so it does not bulk-download. A public deployment should keep that behavior and respect each service's terms.
- **Prompt injection through the AI parser.** Someone could type "ignore your instructions and..." into the mood box. *Prevention (done):* the typed text is sent only as data inside `<request>` tags (angle brackets stripped so it cannot close the tag), the prompt tells the model to ignore instructions inside it, and, most importantly, the model's reply can only become six numbers and a few genre words, which are validated and clamped. It has no tools and cannot make the app do anything but rank songs. A test checks that absurd output (`energy = 1e12`) still produces safe results.
- **A leaked or abused API key.** A key committed to a public repo can be stolen, and a public app lets strangers spend my quota. *Prevention (done):* the key is read only from the environment, a git-ignored `.env`, or Streamlit secrets, never from code. The app caps AI requests at 20 per session, caches repeats, limits input to 100 characters, and falls back to free keyword matching when the quota runs out.
- **Privacy.** The app does not store searches or user data, but with the AI parser on, the typed mood text is sent to Groq. If someone later added accounts or listening history, that data would need consent and clear limits on what it can be used for.

## 12. What Surprised Me While Testing Reliability

- **The first results were technically correct and still bad.** Searching "Starboy" returned ten songs, all by The Weeknd. Every one scored high, and the system was "working," but the list was useless. I would not have seen this from a number. I had to read the actual output, which led to the 2-songs-per-artist rule.
- **A perfect score hid a problem.** Every mood result showed `sim = 1.00`. The bonuses pushed raw scores above 1 and the display capped them, so all ten songs looked equally perfect. After scaling, scores range from 0.94 to 0.96, which is honest.
- **Real data is messier than it looks.** Only 156 of the 1,000 Spotify songs matched MusicOSet, only about 55% of tracks had album art, and one song had a tempo of exactly 0. I expected merging two CSVs to be easy, and it was most of the work.
- **Writing tests found bugs that manual checks missed.** I had tried many queries by hand and they looked fine. The automated tests then found three more problems: the tempo of 0, a score of `1.0000001` from float rounding, and "Seed-Song" not matching "Seed Song" because hyphens were deleted. The suite now has 174 tests plus a 52-check evaluation script, and all pass, but the lesson is that "it looked right to me" was not enough. I also added negative controls (for example, confirming that explicit songs *do* appear when the filter is off) because a test that can never fail proves nothing.
- **Fitting the numbers is not the same as sounding right.** The tests prove that "workout" results have high energy and "sleep" results have low energy. They cannot prove that a person would enjoy the songs. That judgment still needs a human, which is why the previews are in the app.

## 13. My Collaboration with AI

I used Claude as a coding partner for most of MatrixMix. I set the goal and made the decisions, and the AI wrote and ran code, found problems in its own output and explained trade-offs. I also kept a hand on the controls. For example, when the AI started to run commands across my git folders without explaining why, I stopped it and asked what it planned to do, and only let it continue once the plan was clear.

**A suggestion I accepted: using MusicOSet's real audio features for mood search.**
When I asked how to make recommendations "based on mood more," the AI pointed out that my datasets had no mood or audio data at all, so "chill" had nothing to match against. It offered three routes and said real audio features (energy, valence, acousticness, tempo) would be the biggest improvement, and that MusicOSet ships them in a separate folder I had not downloaded. I added the `musicoset_songfeatures` folder. This worked well because "chill" became something measurable, and it lets the app show *why* a song fits ("energy 0.36, acoustic 0.66, tempo 84 bpm"). That explanation is the part I like best about the system.

**A suggestion I did not accept as written, then revised: having an LLM turn free text into a mood profile.**
The AI's third option was to send the user's sentence ("a chill song to play in a cafe") to an LLM, which would return a structured profile and handle any phrasing, including words I never listed. At first I rejected it and chose keyword matching only: it was free, worked offline, gave the same answer every time, and was easy to test. Cost was a real factor. When I asked whether using the API key would cost money, the answer was yes for the Claude API (it is pay-per-use, separate from a Claude subscription), and a public app could be spammed into running up a bill.

Later, once the guardrails and tests were in place, I wanted a real AI feature, so I revisited it, but not as the AI first described it. I changed three things. First, I chose Groq, which has a free tier, after a mix-up where the AI assumed a Google Gemini key and I corrected it ("I meant another company's API key"). Second, the LLM does not replace the keyword parser: it is used first when a key exists, and keyword matching is kept as an automatic fallback, so the app still works with no key, no network or a failed call. Third, the model only returns numbers (target audio features) and the existing ranker picks the songs, so the model cannot invent songs, and I validate and clamp everything it returns because I treat the reply as untrusted. I also stopped the AI when it tried to look something up before I had clarified which company's key I meant, and asked it to commit the earlier work first, so each step stayed a separate, reviewable change.

**Where the AI was wrong, and how it got caught.** The AI also made mistakes that I only found because I checked its work:
- Its first recommender returned ten songs by one artist.
- Its mood scores all showed 1.00.
- The `python -m src.main` command in the old README did not run.
- At one point it mixed a shell command into a git commit message.

Each time, reading real output, running the tests or looking at the git history caught it. I do not treat the AI's output as correct until it has been run and checked.

## 14. What I Would Do Next

- Find explicit-content flags for the songs that only appear in the Spotify top-1000 list, which are currently unfiltered.
- Use the audio features in song-to-song mode too, so similar songs also sound similar.
- Add a recency control so users can ask for newer music, and down-rank karaoke and cast-recording "artists."
- Add more live evaluation phrasings for the AI parser. The first live run passed, but only four cases were covered.
- Test the AI parser on non-English requests and on odd or adversarial text, which the live checks do not cover.
- Add automated tests for the cover and preview lookups (the page itself was driven with Streamlit's test harness, but the outside services were only checked by hand), and collect feedback from real listeners so the mood profiles are based on what people say, not my guesses.
