import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
import re
import requests
import threading
from pathlib import Path
from collections import Counter

# =========================
# PAGE CONFIG
# =========================

st.set_page_config(page_title="🐦 Twitter Vault", page_icon="🐦", layout="centered")

st.markdown("""
<style>
/* ── Layout ── */
.block-container{
    padding-top:7.2rem;
    padding-bottom:0.4rem;
}
[data-testid="stSidebar"]{display:none!important;}
[data-testid="collapsedControl"]{display:none!important;}
header[data-testid="stHeader"]{background:transparent!important;border:none!important;box-shadow:none!important;}
#top-nav-marker + div div[data-testid="stHorizontalBlock"]{
    flex-wrap:nowrap!important;
    gap:8px;
    position:fixed;
    top:2.875rem;
    left:0;
    right:0;
    z-index:999;
    background:#0b1020;
    padding:6px 12px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    box-shadow: 0 4px 20px rgba(0,0,0,0.35);
}
div[data-testid="stHorizontalBlock"]>div[data-testid="stColumn"]{min-width:0;overflow:hidden;}

/* ── All buttons: compact base ── */
.stButton>button{
    min-height:36px;
    font-size:0.88rem;
    border-radius:9px!important;
    transition:filter .12s ease,transform .08s ease;
}
.stButton>button:active{filter:brightness(.8);transform:scale(.96);}

/* ── Nav buttons ── */
#top-nav-marker + div div[data-testid="stHorizontalBlock"] .stButton>button{
    min-height:60px!important;
    font-size:1.3rem!important;
}

/* ── Restore normal sizes for Random-page controls ── */
#top-nav-marker ~ div .rnd-hero .stButton>button{
    min-height:62px!important;
    font-size:1.18rem!important;
    font-weight:700!important;
    border-radius:18px!important;
}
#top-nav-marker ~ div .rnd-actions .stButton>button{
    min-height:52px!important;
    font-size:1.4rem!important;
    border-radius:14px!important;
    background:rgba(255,255,255,0.07)!important;
    border:1px solid rgba(255,255,255,0.10)!important;
    color:rgba(255,255,255,0.8)!important;
}
#top-nav-marker ~ div .rnd-actions .stButton>button[kind="primary"]{
    background:rgba(29,155,240,0.85)!important;
    border-color:transparent!important;
    color:#fff!important;
}

/* ── Random-page hero card ── */
.rnd-card{
    background: linear-gradient(145deg,rgba(29,155,240,0.12) 0%,rgba(20,20,40,0.9) 100%);
    border: 1px solid rgba(29,155,240,0.3);
    border-radius: 18px;
    padding: 20px 18px 16px;
    margin-bottom: 8px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.5);
    min-height: 140px;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
}
.placeholder-card {
    background: linear-gradient(145deg, rgba(255,255,255,0.03) 0%, rgba(10,10,20,0.6) 100%) !important;
    border: 1px dashed rgba(255,255,255,0.15) !important;
}
.rnd-text{
    font-size: 0.95rem;
    font-weight: 400;
    line-height: 1.45;
    word-break: break-word;
    margin-bottom: 8px;
    color: rgba(255,255,255,0.92);
    display: -webkit-box;
    -webkit-line-clamp: 5;
    -webkit-box-orient: vertical;
    overflow: hidden;
}
.rnd-id{
    color: rgba(255,255,255,0.35);
    font-size: 0.72rem;
    margin-bottom: 0;
    letter-spacing: 0.03em;
}
.rnd-badge-fav{ color:#f5a623; }
.rnd-badge-del{ color:rgba(255,255,255,0.35); }

/* ── Tweet list cards ── */
.tweet-info{
    padding:0;
    display:flex;
    flex-direction:column;
    justify-content:center;
    min-height:38px;
}
.tweet-text{
    font-size:0.88rem;
    line-height:1.35;
    word-break:break-word;
    overflow:hidden;
    display:-webkit-box;
    -webkit-line-clamp:2;
    -webkit-box-orient:vertical;
    color:rgba(255,255,255,0.88);
}
.tweet-meta{
    color:rgba(255,255,255,0.38);
    font-size:0.62rem;
    margin-top:2px;
    letter-spacing:0.01em;
    font-family:monospace;
}
.tweet-badge-fav{color:#f5a623;}
.tweet-badge-del{opacity:0.45;}

/* ── Card container ── */
[data-testid="stVerticalBlockBorderWrapper"]{
    border-radius:16px!important;
    overflow:hidden;
}
[data-testid="stVerticalBlockBorderWrapper"]>div{
    padding:10px 14px!important;
    gap:0!important;
}

/* ── Inline action buttons ── */
.tweet-action-btn .stButton>button{
    min-height:44px!important;
    font-size:1.3rem!important;
    font-family:"Apple Color Emoji","Segoe UI Emoji","Noto Color Emoji",sans-serif!important;
    padding:4px 2px!important;
    border-radius:10px!important;
    background:rgba(255,255,255,0.06)!important;
    border:none!important;
    color:rgba(255,255,255,0.7)!important;
    box-shadow:none!important;
    overflow:visible!important;
    line-height:1.4!important;
}
.tweet-action-btn .stButton>button:hover{
    background:rgba(255,255,255,0.12)!important;
}
.tweet-action-btn .stButton>button[kind="primary"]{
    background:#1D9BF0!important;
    color:#fff!important;
    border:none!important;
}
button[kind="secondary"]{
    background:rgba(255,255,255,0.03)!important;
    border:none!important;
}

/* ── Open button ── */
a.custom-open-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    min-height: 38px;
    background-color: #1D9BF0 !important;
    color: #ffffff !important;
    border-radius: 9px !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    text-decoration: none !important;
    border: none !important;
    cursor: pointer !important;
    text-align: center !important;
    box-sizing: border-box !important;
    padding: 6px 16px !important;
    transition: filter 0.12s ease, transform 0.08s ease !important;
}
a.custom-open-btn:hover {
    filter: brightness(1.1) !important;
    color: #ffffff !important;
    text-decoration: none !important;
}
a.custom-open-btn:active {
    filter: brightness(0.8) !important;
    transform: scale(0.96) !important;
}

a.custom-open-btn-inline {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    min-height: 36px;
    background-color: #1D9BF0 !important;
    color: #ffffff !important;
    border-radius: 9px !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    text-decoration: none !important;
    border: none !important;
    cursor: pointer !important;
    text-align: center !important;
    box-sizing: border-box !important;
    padding: 4px 8px !important;
    transition: filter 0.12s ease, transform 0.08s ease !important;
}
a.custom-open-btn-inline:hover {
    filter: brightness(1.1) !important;
    color: #ffffff !important;
    text-decoration: none !important;
}
a.custom-open-btn-inline:active {
    filter: brightness(0.8) !important;
    transform: scale(0.96) !important;
}

/* ── Hashtag pills ── */
.hashtag-pill {
    display: inline-block;
    background: rgba(29,155,240,0.15);
    border: 1px solid rgba(29,155,240,0.3);
    border-radius: 50px;
    padding: 3px 10px;
    font-size: 0.8rem;
    color: #1D9BF0;
    margin: 2px 3px;
    cursor: pointer;
}

@media(max-width:640px){
    .block-container{padding-left:0.5rem;padding-right:0.5rem;}
}
</style>
""", unsafe_allow_html=True)

# =========================
# HELPERS
# =========================

def get_twitter_url(tweet_id: str) -> str:
    return f"intent://twitter.com/i/web/status/{tweet_id}#Intent;package=com.twitter.android;scheme=https;end;"

def tw_open_button(tweet_id: str, label: str = "🐦 Open in X"):
    url = get_twitter_url(tweet_id)
    st.markdown(f'<a href="{url}" target="_blank" class="custom-open-btn">{label}</a>', unsafe_allow_html=True)

def extract_hashtags(text: str):
    return [t.lower() for t in re.findall(r"#(\w+)", text)]

def extract_mentions(text: str):
    return [m.lower() for m in re.findall(r"@(\w+)", text)]

def clean_text_preview(text: str) -> str:
    text = re.sub(r"https?://\S+", "", text).strip()
    return text or "(media/link only)"

# =========================
# PERSISTENCE
# =========================

MARKERS_FILE = Path.home() / ".twitter_vault_markers.json"

def _get_secret(key, default=""):
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default

def load_markers():
    gist_id = _get_secret("GIST_ID")
    token   = _get_secret("GITHUB_TOKEN")
    if gist_id and token:
        try:
            resp = requests.get(
                f"https://api.github.com/gists/{gist_id}",
                headers={"Authorization": f"token {token}"},
                timeout=5,
            )
            if resp.status_code == 200:
                files = resp.json().get("files", {})
                if "twitter_vault.json" in files:
                    data = json.loads(files["twitter_vault.json"]["content"])
                    return set(data.get("favourites", [])), set(data.get("probably_deleted", []))
        except Exception:
            pass
    if MARKERS_FILE.exists():
        try:
            data = json.loads(MARKERS_FILE.read_text(encoding="utf-8"))
            return set(data.get("favourites", [])), set(data.get("probably_deleted", []))
        except Exception:
            pass
    return set(), set()

def _gist_push(payload: str):
    gist_id = _get_secret("GIST_ID")
    token   = _get_secret("GITHUB_TOKEN")
    if gist_id and token:
        try:
            requests.patch(
                f"https://api.github.com/gists/{gist_id}",
                headers={"Authorization": f"token {token}"},
                json={"files": {"twitter_vault.json": {"content": payload}}},
                timeout=8,
            )
        except Exception:
            pass

def save_markers(favourites: set, probably_deleted: set):
    payload = json.dumps({"favourites": list(favourites), "probably_deleted": list(probably_deleted)})
    try:
        MARKERS_FILE.write_text(payload, encoding="utf-8")
    except Exception:
        pass
    threading.Thread(target=_gist_push, args=(payload,), daemon=True).start()

# =========================
# LOAD DATA (cached once)
# =========================

LIKE_JS = Path(__file__).parent / "twitter-2026-05-25-99e1dcfe09317b1d745fc9e7591285b5bb82428605d670680570aed788975f95" / "data" / "like.js"

@st.cache_data
def load_data():
    raw = LIKE_JS.read_text(encoding="utf-8")
    # Strip JS variable assignment: window.YTD.like.part0 = [...]
    raw = re.sub(r"^window\.YTD\.like\.part\d+\s*=\s*", "", raw.strip()).rstrip(";")
    records = json.loads(raw)
    rows = []
    for i, rec in enumerate(records):
        like = rec["like"]
        rows.append({
            "id":           i + 1,
            "tweet_id":     like["tweetId"],
            "full_text":    like.get("fullText", ""),
            "preview_text": clean_text_preview(like.get("fullText", "")),
            "url":          like.get("expandedUrl", f"https://x.com/i/web/status/{like['tweetId']}"),
        })
    df = pd.DataFrame(rows)
    return df

@st.cache_data
def build_hashtag_index(_df):
    counter = Counter()
    for text in _df["full_text"]:
        counter.update(extract_hashtags(text))
    return counter

@st.cache_data
def build_mention_index(_df):
    counter = Counter()
    for text in _df["full_text"]:
        counter.update(extract_mentions(text))
    return counter

df = load_data()
hashtag_counts = build_hashtag_index(df)
mention_counts = build_mention_index(df)

# =========================
# SESSION STATE
# =========================

if "favourites" not in st.session_state:
    favs, pdels = load_markers()
    st.session_state.favourites       = favs
    st.session_state.probably_deleted = pdels

# =========================
# NAVIGATION
# =========================

PAGES     = ["🎲 Random", "🔍 Search", "#️⃣ Hashtags", "📊 Stats", "★ Favourites", "🗑 Deleted"]
NAV_ICONS = ["🎲",        "🔍",        "#️⃣",           "📊",       "★",            "🗑"]

if "nav_page" not in st.session_state:
    st.session_state.nav_page = PAGES[0]

if "_pending_nav" in st.session_state:
    st.session_state.nav_page = st.session_state.pop("_pending_nav")

page = st.session_state.nav_page

# =========================
# TOP NAV
# =========================

st.markdown('<div id="top-nav-marker"></div>', unsafe_allow_html=True)
_nav_cols = st.columns(6)
for _i, (_col, _ico, _p) in enumerate(zip(_nav_cols, NAV_ICONS, PAGES)):
    with _col:
        if st.button(
            _ico,
            key=f"topnav_{_i}",
            type="primary" if page == _p else "secondary",
            use_container_width=True,
            help=_p,
        ):
            st.session_state.nav_page = _p
            st.rerun()

# =========================
# DIALOG
# =========================

@st.dialog("🐦 Tweet Details")
def tweet_dialog(row_dict):
    post_id = row_dict["id"]
    is_fav  = post_id in st.session_state.favourites
    is_del  = post_id in st.session_state.probably_deleted

    st.markdown(
        f"<div style='font-size:0.93rem;line-height:1.5;word-break:break-word;padding:4px 0 12px 0'>"
        f"{row_dict['full_text']}"
        f"</div>",
        unsafe_allow_html=False,
    )
    st.caption(f"ID: {row_dict['tweet_id']}")

    tags = extract_hashtags(row_dict["full_text"])
    if tags:
        st.caption("Hashtags: " + "  ".join(f"#{t}" for t in tags[:10]))

    tw_open_button(row_dict["tweet_id"])
    st.divider()

    col_fav, col_del = st.columns(2)
    with col_fav:
        if st.button(
            "★ Favourited" if is_fav else "☆ Favourite",
            key=f"dlg_fav_{post_id}",
            type="primary" if is_fav else "secondary",
            use_container_width=True,
        ):
            st.session_state.favourites.discard(post_id)
            st.session_state.probably_deleted.discard(post_id)
            if not is_fav:
                st.session_state.favourites.add(post_id)
            save_markers(st.session_state.favourites, st.session_state.probably_deleted)
            st.rerun()
    with col_del:
        if st.button(
            "🗑 Marked" if is_del else "🗑 Prob. Deleted",
            key=f"dlg_del_{post_id}",
            type="primary" if is_del else "secondary",
            use_container_width=True,
        ):
            st.session_state.favourites.discard(post_id)
            st.session_state.probably_deleted.discard(post_id)
            if not is_del:
                st.session_state.probably_deleted.add(post_id)
            save_markers(st.session_state.favourites, st.session_state.probably_deleted)
            st.rerun()

# =========================
# CARD GRID FRAGMENT
# =========================

@st.fragment
def render_card_grid(filtered_df, per_page, page_key, key_prefix):
    total_posts = len(filtered_df)
    if total_posts == 0:
        st.info("No tweets match your filters.")
        return

    total_pages  = max(1, -(-total_posts // per_page))
    current_page = min(st.session_state.get(page_key, 0), total_pages - 1)
    st.session_state[page_key] = current_page

    def pagination_row(suffix):
        c_prev, c_info, c_next = st.columns([1, 3, 1])
        with c_prev:
            if st.button("◀", key=f"prev_{suffix}_{page_key}",
                         disabled=(current_page == 0), use_container_width=True):
                st.session_state[page_key] -= 1
                st.rerun()
        with c_info:
            st.markdown(
                f"<p style='text-align:center;margin:10px 0 0 0;font-size:0.9rem'>"
                f"{current_page + 1} / {total_pages:,}</p>",
                unsafe_allow_html=True,
            )
        with c_next:
            if st.button("▶", key=f"next_{suffix}_{page_key}",
                         disabled=(current_page >= total_pages - 1), use_container_width=True):
                st.session_state[page_key] += 1
                st.rerun()

    st.caption(f"{total_posts:,} tweets")
    pagination_row("top")

    new_p = st.selectbox(
        "page picker",
        options=list(range(1, total_pages + 1)),
        index=current_page,
        key=f"goto_{page_key}_{current_page}",
        format_func=lambda x: f"Page {x:,}",
        label_visibility="collapsed",
    )
    if new_p - 1 != current_page:
        st.session_state[page_key] = new_p - 1
        st.rerun()

    page_df = filtered_df.iloc[current_page * per_page : (current_page + 1) * per_page]
    favs    = st.session_state.favourites
    pdels   = st.session_state.probably_deleted

    for _, row in page_df.iterrows():
        post_id  = row["id"]
        is_fav   = post_id in favs
        is_del   = post_id in pdels

        preview = row["preview_text"]
        preview_display = (preview[:80] + "…") if len(preview) > 81 else preview

        if is_fav:
            badge_html = " <span class='tweet-badge-fav'>★</span>"
        elif is_del:
            badge_html = " <span class='tweet-badge-del'>🗑</span>"
        else:
            badge_html = ""

        with st.container(border=True):
            c_info, c_fav, c_del, c_more, c_open = st.columns([5, 2, 2, 2, 4], vertical_alignment="center")

            with c_info:
                st.markdown(
                    f"<div class='tweet-info'>"
                    f"<div class='tweet-text'>{preview_display}{badge_html}</div>"
                    f"<div class='tweet-meta'>{row['tweet_id']}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            with c_fav:
                fav_active = post_id in favs
                st.markdown('<div class="tweet-action-btn">', unsafe_allow_html=True)
                if st.button("★" if fav_active else "☆", key=f"fav_inline_{key_prefix}_{post_id}",
                             use_container_width=True, type="primary" if fav_active else "secondary"):
                    pdels.discard(post_id)
                    if fav_active:
                        favs.discard(post_id)
                    else:
                        favs.add(post_id)
                    save_markers(favs, pdels)
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            with c_del:
                del_active = post_id in pdels
                st.markdown('<div class="tweet-action-btn">', unsafe_allow_html=True)
                if st.button("🗑", key=f"del_inline_{key_prefix}_{post_id}",
                             use_container_width=True, type="primary" if del_active else "secondary"):
                    favs.discard(post_id)
                    if del_active:
                        pdels.discard(post_id)
                    else:
                        pdels.add(post_id)
                    save_markers(favs, pdels)
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            with c_more:
                st.markdown('<div class="tweet-action-btn">', unsafe_allow_html=True)
                if st.button("⋮", key=f"menu_{key_prefix}_{post_id}", use_container_width=True):
                    tweet_dialog(row.to_dict())
                st.markdown('</div>', unsafe_allow_html=True)

            with c_open:
                btn_html = f'<a href="{get_twitter_url(row["tweet_id"])}" target="_blank" class="custom-open-btn-inline">Open</a>'
                st.markdown(btn_html, unsafe_allow_html=True)

    pagination_row("bot")

# =========================
# RANDOM PAGE
# =========================

if page == "🎲 Random":

    _pool_options = ["All likes", "★ Favourites only", "🗑 Probably Deleted"]
    _pool_sel = st.selectbox(
        "Pick from",
        options=_pool_options,
        key="rnd_pool_select",
        label_visibility="collapsed",
    )

    col_left, col_right = st.columns(2)
    has_post = "random_tweet" in st.session_state

    with col_left:
        if has_post:
            post    = st.session_state.random_tweet
            post_id = post["id"]
            favs    = st.session_state.favourites
            pdels   = st.session_state.probably_deleted
            is_fav  = post_id in favs
            is_del  = post_id in pdels
            badge   = (
                " <span class='rnd-badge-fav'>★</span>" if is_fav
                else " <span class='rnd-badge-del'>🗑</span>" if is_del
                else ""
            )
            preview_full = post["preview_text"] or post["full_text"][:200]
            st.markdown(
                f"""<div class="rnd-card">
                    <div class="rnd-text">{preview_full}{badge}</div>
                    <div class="rnd-id">ID: {post['tweet_id']}</div>
                </div>""",
                unsafe_allow_html=True,
            )
            st.markdown('<div class="rnd-actions">', unsafe_allow_html=True)
            _ac1, _ac2, _ac3 = st.columns([1, 1, 1])
            with _ac1:
                if st.button("★" if is_fav else "☆", key="rnd_fav",
                             type="primary" if is_fav else "secondary",
                             use_container_width=True):
                    favs.discard(post_id); pdels.discard(post_id)
                    if not is_fav: favs.add(post_id)
                    save_markers(favs, pdels); st.rerun()
            with _ac2:
                if st.button("🗑", key="rnd_del",
                             type="primary" if is_del else "secondary",
                             use_container_width=True):
                    favs.discard(post_id); pdels.discard(post_id)
                    if not is_del: pdels.add(post_id)
                    save_markers(favs, pdels); st.rerun()
            with _ac3:
                if st.button("⋮", key="rnd_more", use_container_width=True):
                    tweet_dialog(post)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown(
                """<div class="rnd-card placeholder-card">
                    <div class="rnd-text" style="color:rgba(255,255,255,0.3)">No tweet loaded yet</div>
                    <div class="rnd-id" style="color:rgba(255,255,255,0.2)">Tap below to discover</div>
                </div>""",
                unsafe_allow_html=True,
            )
            st.markdown('<div style="height:52px;margin-top:16px;"></div>', unsafe_allow_html=True)

        st.markdown('<div class="rnd-hero">', unsafe_allow_html=True)
        if _pool_sel == "★ Favourites only":
            btn_label = "🎲 Random Favourite"
        elif _pool_sel == "🗑 Probably Deleted":
            btn_label = "🎲 Random Deleted"
        else:
            btn_label = "🎲 Random Like"

        if st.button(btn_label, use_container_width=True, type="primary", key="rnd_open"):
            if _pool_sel == "★ Favourites only":
                pool_df = df[df["id"].isin(st.session_state.favourites)]
            elif _pool_sel == "🗑 Probably Deleted":
                pool_df = df[df["id"].isin(st.session_state.probably_deleted)]
            else:
                pool_df = df
            if pool_df.empty:
                st.toast("No tweets in this pool yet!", icon="⚠️")
            else:
                st.session_state.random_tweet = pool_df.sample(1).iloc[0].to_dict()
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        if has_post:
            post = st.session_state.random_tweet
            st.markdown('<div style="height:148px;"></div>', unsafe_allow_html=True)
            tw_open_button(post["tweet_id"], label="🐦 Open in X")
            st.markdown('<div style="height:52px;margin-top:16px;"></div>', unsafe_allow_html=True)
        else:
            st.markdown(
                """<div class="rnd-card placeholder-card" style="visibility:hidden;">
                    <div class="rnd-text">Spacer</div>
                    <div class="rnd-id">Spacer</div>
                </div>""",
                unsafe_allow_html=True,
            )
            st.markdown('<div style="height:52px;margin-top:16px;"></div>', unsafe_allow_html=True)

        st.markdown('<div class="rnd-hero">', unsafe_allow_html=True)
        if st.button("🎲 New Random", use_container_width=True, type="secondary", key="rnd_again"):
            if _pool_sel == "★ Favourites only":
                pool_df = df[df["id"].isin(st.session_state.favourites)]
            elif _pool_sel == "🗑 Probably Deleted":
                pool_df = df[df["id"].isin(st.session_state.probably_deleted)]
            else:
                pool_df = df
            if pool_df.empty:
                st.toast("No tweets in this pool yet!", icon="⚠️")
            else:
                st.session_state.random_tweet = pool_df.sample(1).iloc[0].to_dict()
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# =========================
# SEARCH PAGE
# =========================

elif page == "🔍 Search":

    st.title("🔍 Search")

    query = st.text_input("Search tweet text", placeholder="keyword, #hashtag, or @mention…", key="search_input")

    per_page_s = st.selectbox("Per page", [10, 25, 50, 100], index=1, key="search_per_page")

    marker_filter = st.selectbox("Filter", ["All", "Favourites", "Probably Deleted", "Unmarked"], key="search_marker")

    favs  = st.session_state.favourites
    pdels = st.session_state.probably_deleted

    mask = pd.Series([True] * len(df), index=df.index)

    if query:
        mask &= df["full_text"].str.contains(re.escape(query), case=False, na=False)

    if marker_filter == "Favourites":
        mask &= df["id"].isin(favs)
    elif marker_filter == "Probably Deleted":
        mask &= df["id"].isin(pdels)
    elif marker_filter == "Unmarked":
        mask &= ~df["id"].isin(favs | pdels)

    search_sig = (query, per_page_s, marker_filter)
    if st.session_state.get("search_filter_sig") != search_sig:
        st.session_state["search_filter_sig"] = search_sig
        st.session_state["search_page_num"]   = 0

    results = df[mask]
    render_card_grid(results, per_page_s, "search_page_num", "search")

# =========================
# HASHTAGS PAGE
# =========================

elif page == "#️⃣ Hashtags":

    st.title("#️⃣ Hashtags")

    _ht_tab, _mn_tab = st.tabs(["#️⃣ Hashtags", "@ Mentions"])

    with _ht_tab:
        top_n = st.slider("Show top N", 10, 100, 30, key="ht_top_n")
        top_tags = hashtag_counts.most_common(top_n)

        if not top_tags:
            st.info("No hashtags found in your likes.")
        else:
            ht_df = pd.DataFrame(top_tags, columns=["hashtag", "count"])

            st.bar_chart(ht_df.set_index("hashtag"), use_container_width=True)

            st.divider()
            st.caption("Tap a hashtag to browse matching tweets")

            selected_tag = st.session_state.get("selected_hashtag", "")

            cols_per_row = 3
            tag_list = [t for t, _ in top_tags]
            rows = [tag_list[i:i+cols_per_row] for i in range(0, len(tag_list), cols_per_row)]
            for row_tags in rows:
                cols = st.columns(cols_per_row)
                for col, tag in zip(cols, row_tags):
                    with col:
                        cnt = hashtag_counts[tag]
                        is_active = selected_tag == tag
                        if st.button(
                            f"#{tag} ({cnt})",
                            key=f"ht_btn_{tag}",
                            type="primary" if is_active else "secondary",
                            use_container_width=True,
                        ):
                            if is_active:
                                st.session_state["selected_hashtag"] = ""
                            else:
                                st.session_state["selected_hashtag"] = tag
                            st.session_state["ht_page"] = 0
                            st.rerun()

            if selected_tag:
                st.divider()
                st.markdown(f"### #{selected_tag}")
                tag_results = df[df["full_text"].str.contains(f"#{selected_tag}", case=False, na=False)]
                per_page_ht = st.selectbox("Per page", [10, 25, 50], index=1, key="ht_per_page")
                render_card_grid(tag_results, per_page_ht, "ht_page", "ht")

    with _mn_tab:
        top_m = st.slider("Show top N", 10, 100, 30, key="mn_top_n")
        top_mentions = mention_counts.most_common(top_m)

        if not top_mentions:
            st.info("No @mentions found in your likes.")
        else:
            mn_df = pd.DataFrame(top_mentions, columns=["mention", "count"])
            st.bar_chart(mn_df.set_index("mention"), use_container_width=True)

            st.divider()
            st.caption("Tap a mention to browse matching tweets")

            selected_mention = st.session_state.get("selected_mention", "")

            cols_per_row = 3
            mention_list = [m for m, _ in top_mentions]
            m_rows = [mention_list[i:i+cols_per_row] for i in range(0, len(mention_list), cols_per_row)]
            for m_row in m_rows:
                cols = st.columns(cols_per_row)
                for col, mention in zip(cols, m_row):
                    with col:
                        cnt = mention_counts[mention]
                        is_active = selected_mention == mention
                        if st.button(
                            f"@{mention} ({cnt})",
                            key=f"mn_btn_{mention}",
                            type="primary" if is_active else "secondary",
                            use_container_width=True,
                        ):
                            if is_active:
                                st.session_state["selected_mention"] = ""
                            else:
                                st.session_state["selected_mention"] = mention
                            st.session_state["mn_page"] = 0
                            st.rerun()

            if selected_mention:
                st.divider()
                st.markdown(f"### @{selected_mention}")
                mention_results = df[df["full_text"].str.contains(f"@{selected_mention}", case=False, na=False)]
                per_page_mn = st.selectbox("Per page", [10, 25, 50], index=1, key="mn_per_page")
                render_card_grid(mention_results, per_page_mn, "mn_page", "mn")

# =========================
# STATS PAGE
# =========================

elif page == "📊 Stats":

    st.title("📊 Stats")

    favs  = st.session_state.favourites
    pdels = st.session_state.probably_deleted

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Total Liked", f"{len(df):,}")
        st.metric("Favourited",  f"{len(favs):,}")
    with c2:
        st.metric("Unique Hashtags",  f"{len(hashtag_counts):,}")
        st.metric("Prob. Deleted",    f"{len(pdels):,}")

    st.divider()
    st.subheader("🔝 Top 20 Hashtags")
    top20_ht = pd.DataFrame(hashtag_counts.most_common(20), columns=["hashtag", "count"])
    if not top20_ht.empty:
        st.bar_chart(top20_ht.set_index("hashtag"), use_container_width=True)

    st.divider()
    st.subheader("🔝 Top 20 Mentions")
    top20_mn = pd.DataFrame(mention_counts.most_common(20), columns=["mention", "count"])
    if not top20_mn.empty:
        st.bar_chart(top20_mn.set_index("mention"), use_container_width=True)

    st.divider()
    st.subheader("📏 Tweet Length Distribution")
    _len_df = df.copy()
    _len_df["text_len"] = _len_df["full_text"].str.len()
    _bins = pd.cut(_len_df["text_len"], bins=[0, 50, 100, 150, 200, 280, 500, 5000],
                   labels=["<50", "50-100", "100-150", "150-200", "200-280", "280-500", "500+"])
    _len_chart = _bins.value_counts().sort_index().reset_index()
    _len_chart.columns = ["Length", "Count"]
    st.bar_chart(_len_chart.set_index("Length"), use_container_width=True)

    st.divider()
    st.subheader("🔖 Markers")
    st.caption(f"★ Favourites: {len(favs):,}  ·  🗑 Prob. Deleted: {len(pdels):,}")
    with st.expander("Clear markers"):
        if st.button("Clear Favourites", use_container_width=True):
            st.session_state.favourites = set()
            save_markers(st.session_state.favourites, st.session_state.probably_deleted)
            st.rerun()
        if st.button("Clear Prob. Deleted", use_container_width=True):
            st.session_state.probably_deleted = set()
            save_markers(st.session_state.favourites, st.session_state.probably_deleted)
            st.rerun()

# =========================
# FAVOURITES PAGE
# =========================

elif page == "★ Favourites":

    st.title("★ Favourites")

    favs  = st.session_state.favourites
    pdels = st.session_state.probably_deleted

    fav_df = df[df["id"].isin(favs)]

    if fav_df.empty:
        st.info("No favourites yet. Star tweets on any page to save them here.")
    else:
        st.caption(f"{len(fav_df):,} favourited tweets")
        per_page_f = st.selectbox("Per page", [10, 25, 50, 100], index=1, key="fav_per_page")
        render_card_grid(fav_df, per_page_f, "fav_page", "fav")

# =========================
# DELETED PAGE
# =========================

elif page == "🗑 Deleted":

    st.title("🗑 Deleted")

    favs  = st.session_state.favourites
    pdels = st.session_state.probably_deleted

    del_df = df[df["id"].isin(pdels)]

    _dl, _dr = st.columns([3, 2])
    with _dl:
        st.caption(f"{len(del_df):,} tweets marked deleted")
    with _dr:
        if st.button("🧹 Purge All", key="purge_btn", type="secondary", use_container_width=True):
            st.session_state["purge_confirm"] = True

    # ── Purge confirmation ──
    if st.session_state.get("purge_confirm"):
        st.warning(
            f"This will permanently remove all **{len(pdels):,} deleted** markers from your "
            f"local file and GitHub Gist. The tweets remain in your Twitter account. "
            f"This cannot be undone.",
            icon="⚠️",
        )
        _pc1, _pc2 = st.columns(2)
        with _pc1:
            if st.button("Yes, purge all", key="purge_yes", type="primary", use_container_width=True):
                st.session_state.probably_deleted = set()
                save_markers(st.session_state.favourites, set())
                st.session_state.pop("purge_confirm", None)
                st.toast(f"Purged {len(del_df):,} deleted markers.", icon="🧹")
                st.rerun()
        with _pc2:
            if st.button("Cancel", key="purge_cancel", use_container_width=True):
                st.session_state.pop("purge_confirm", None)
                st.rerun()

    if del_df.empty:
        st.info("No tweets marked as deleted yet. Tap 🗑 on any tweet to mark it.")
    else:
        per_page_d = st.selectbox("Per page", [10, 25, 50, 100], index=1, key="del_per_page")
        render_card_grid(del_df, per_page_d, "del_page", "del")
