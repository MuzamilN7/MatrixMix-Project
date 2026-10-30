# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

Give your model a short, descriptive name.  
Example: **VibeFinder 1.0**  

---

## 2. Intended Use  

Describe what your recommender is designed to do and who it is for. 

Prompts:  

- What kind of recommendations does it generate  
- What assumptions does it make about the user  
- Is this for real users or classroom exploration  

---

## 3. How the Model Works  

The recommender works like a points game. You tell it what you are in the mood for, it gives every song in the catalog a score for how well it fits, and it shows you the highest scorers.

**What it looks at in a song:** its mood (like "chill" or "happy"), its genre (like "lofi" or "pop"), and a few numbers describing how it sounds: energy, valence (how upbeat or gloomy it feels), tempo, danceability, and acousticness (how acoustic versus electronic it is).

**What you tell it:** your favorite mood and genre, plus how high or low you want each of those numbers to be. You can leave any of them out, and the recommender simply skips what you did not mention.

**How a song earns points:**

- **Mood match: up to 3 points.** The biggest prize, because mood describes what you want to hear right now. It is all or nothing: the song's mood either matches yours or it doesn't.
- **Genre match: up to 2 points.** Also all or nothing, but worth less, since people will often enjoy a song outside their usual genre if the vibe is right.
- **Energy: up to 1.5 points.** The closer the song's energy is to what you asked for, the more points it gets. A song that is spot on gets all 1.5, and one that is far off gets almost none.
- **Valence, tempo, danceability and acousticness: up to 0.5 points each.** These work like energy (closer is better) but count for less.

The most a song can score is 8.5 points. The points add up, and the songs are sorted from highest to lowest. The top few are shown along with the reasons, for example "Mood match (+3)", so you can see exactly why a song was picked.

**A key idea:** for the number-based features, "closer to what you want" beats "higher is better". If you ask for calm music with an energy of 0.3, a song with 0.9 energy is penalized just as a song with 0.0 would be.

**What changed from the starter code:** the starter had empty placeholders for loading songs, scoring them, and ranking them. I filled these in: the loader reads the song file and turns the numbers into real numbers, the scorer applies the point rules above and records a reason for each point earned, and the ranker scores every song and returns the best ones. I also chose the point values so that mood counts the most, followed by genre and energy, and the remaining features act as tie-breakers.

---

## 4. Data  

Describe the dataset the model uses.  

Prompts:  

- How many songs are in the catalog  
- What genres or moods are represented  
- Did you add or remove data  
- Are there parts of musical taste missing in the dataset  

---

## 5. Strengths  

Where does your system seem to work well  

Prompts:  

- User types for which it gives reasonable results  
- Any patterns you think your scoring captures correctly  
- Cases where the recommendations matched your intuition  

---

## 6. Limitations and Bias 

Where the system struggles or behaves unfairly. 

Prompts:  

- Features it does not consider  
- Genres or moods that are underrepresented  
- Cases where the system overfits to one preference  
- Ways the scoring might unintentionally favor some users  

---

## 7. Evaluation  

How you checked whether the recommender behaved as expected. 

Prompts:  

- Which user profiles you tested  
- What you looked for in the recommendations  
- What surprised you  
- Any simple tests or comparisons you ran  

No need for numeric metrics unless you created some.

---

## 8. Future Work  

Ideas for how you would improve the model next.  

Prompts:  

- Additional features or preferences  
- Better ways to explain recommendations  
- Improving diversity among the top results  
- Handling more complex user tastes  

---

## 9. Personal Reflection  

A few sentences about your experience.  

Prompts:  

- What you learned about recommender systems  
- Something unexpected or interesting you discovered  
- How this changed the way you think about music recommendation apps  
