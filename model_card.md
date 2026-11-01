# 🎧 Model Card: Music Recommender Simulation

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