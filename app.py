"""Streamlit app: type a song, get the 10 most similar songs with album covers.

Run:  streamlit run app.py
"""
import re
import sys
from pathlib import Path

import requests
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent / "src"))
from mood import recommend_by_mood  # noqa: E402
from similar import SongSimilarity  # noqa: E402

st.set_page_config(page_title="MatrixMix", page_icon="🎵", layout="wide")
st.markdown(f"<style>{(Path(__file__).parent / 'style.css').read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


@st.cache_resource(show_spinner="Building similarity matrix...")
def get_model() -> SongSimilarity:
    return SongSimilarity()


@st.cache_data(show_spinner=False)
def cover_from_spotify(spotify_id: str) -> str | None:
    """Fallback: ask Spotify's public oEmbed endpoint for the cover of a track."""
    try:
        r = requests.get(
            "https://open.spotify.com/oembed",
            params={"url": f"https://open.spotify.com/track/{spotify_id}"},
            timeout=5,
        )
        return r.json().get("thumbnail_url") if r.ok else None
    except (requests.RequestException, ValueError):
        return None


def cover(row) -> str | None:
    """Album cover URL: the MusicOSet image if we have one, else Spotify oEmbed."""
    url = row["image_url"]
    if isinstance(url, str) and url:
        return url
    return cover_from_spotify(row["spotify_id"])


def show_cover(row, width=None):
    url = cover(row)
    if url:
        st.image(url, width=width, use_container_width=width is None)
    else:
        st.markdown("🎵 *no cover*")


PREVIEW_START, PREVIEW_END = 10, 20  # seconds into iTunes' 30s clip -> a 10s snippet from the middle


@st.cache_data(show_spinner=False)
def preview_url(title: str, artist: str) -> str | None:
    """Find a 30s preview clip via the free iTunes Search API (no key needed)."""
    clean = re.split(r" \(| - ", title)[0]
    first_artist = artist.split(",")[0]
    try:
        r = requests.get(
            "https://itunes.apple.com/search",
            params={"term": f"{clean} {first_artist}", "entity": "song", "limit": 5},
            timeout=5,
        )
        for hit in r.json().get("results", []) if r.ok else []:
            if first_artist.lower() in hit.get("artistName", "").lower() and hit.get("previewUrl"):
                return hit["previewUrl"]
    except (requests.RequestException, ValueError):
        pass
    return None


def preview_button(row, key: str):
    """A Preview button that, once clicked, plays a 10-second snippet under the cover."""
    if st.button("▶ Preview", key=f"btn_{key}_{row['spotify_id']}", use_container_width=True):
        st.session_state["previewing"] = (key, row["spotify_id"])
    if st.session_state.get("previewing") == (key, row["spotify_id"]):
        url = preview_url(row["title"], row["artist"])
        if url:
            st.audio(url, format="audio/mp4", start_time=PREVIEW_START, end_time=PREVIEW_END, autoplay=True)
        else:
            st.caption("No preview available")


def show_grid(recs, key="grid"):
    """Cards are laid out like a 2x5 matrix; each shows its index a_ij, similarity and feature vector."""
    for row_i, start in enumerate(range(0, len(recs), 5)):
        cols = st.columns(5)
        for col_i, (col, (_, r)) in enumerate(zip(cols, recs.iloc[start : start + 5].iterrows())):
            with col, st.container(key=f"card_{key}_{row_i}_{col_i}"):
                st.markdown(f"<span class='mm-idx'>a<sub>{row_i + 1},{col_i + 1}</sub></span>", unsafe_allow_html=True)
                show_cover(r)
                preview_button(r, key)
                st.markdown(f"**{r['title']}**")
                st.caption(f"{r['artist']} · {int(r['year'])}")
                sim = float(max(0, min(1, r["score"])))
                st.markdown(f"<span class='mm-sim'>sim = {sim:.2f}</span>", unsafe_allow_html=True)
                st.progress(sim)
                if r["energy"] == r["energy"]:  # not NaN
                    st.markdown(
                        f"<span class='mm-vec'>v = ⎡{r['energy']:.2f}⎤ energy<br>&nbsp;&nbsp;&nbsp;&nbsp;⎢{r['valence']:.2f}⎥ valence<br>"
                        f"&nbsp;&nbsp;&nbsp;&nbsp;⎣{r['acousticness']:.2f}⎦ acoustic</span>",
                        unsafe_allow_html=True,
                    )
                st.caption(r["why"])


model = get_model()

st.markdown(
    "<div class='mm-title'><div class='mm-bracket'></div>"
    "<div class='mm-name'>MatrixMix<small>find your next song in the similarity matrix</small></div>"
    "<div class='mm-bracket r'></div></div>"
    "<div class='mm-eq'>recommendations = argmax<sub>10</sub>( S · x ) &nbsp;where x = your song or mood vector</div>",
    unsafe_allow_html=True,
)
mode = st.radio("Find music by", ["A song I like", "A mood or vibe"], horizontal=True)

if mode == "A mood or vibe":
    st.caption("Describe what you want, e.g. *a chill song to play in a cafe*, *gym workout*, *sad rainy night*.")
    text = st.text_input("What are you in the mood for?", placeholder="a chill song to play in a cafe")
    if text:
        moods, recs = recommend_by_mood(model.cat, text, k=10)
        if recs.empty:
            st.warning("I didn't recognize a mood in that. Try words like chill, cafe, study, gym, party, sad, happy, road trip.")
        else:
            st.write("Detected: " + ", ".join(f"**{m}**" for m in moods))
            show_grid(recs, "mood")
    st.stop()

st.caption("Give me a song, I'll find 10 that are close to it.")

query = st.text_input("Song name (optionally add the artist)", placeholder="e.g. Starboy")
if query:
    matches = model.search(query)
    if matches.empty:
        st.warning("No songs found. Try another spelling.")
        st.stop()

    labels = {
        i: f"{r.title} — {r.artist} ({int(r.year)})" for i, r in matches.iterrows()
    }
    chosen = st.selectbox("Which one did you mean?", list(labels), format_func=labels.get)
    seed = model.cat.loc[chosen]

    left, right = st.columns([1, 4])
    with left:
        show_cover(seed)
        preview_button(seed, "seed")
    with right:
        st.subheader(seed["title"])
        st.write(f"**{seed['artist']}** · {seed['album']} · {int(seed['year'])}")
        st.write("Genres: " + (", ".join(seed["genres"][:6]) or "unknown"))

    st.divider()
    st.subheader("Songs you might like")
    recs = model.recommend(chosen, k=10)
    show_grid(recs, "song")
