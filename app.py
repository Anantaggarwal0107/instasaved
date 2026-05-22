import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
import requests
import threading
from pathlib import Path

# =========================
# PAGE CONFIG
# =========================

st.set_page_config(page_title="📸 Insta Vault", page_icon="📸", layout="centered")

st.markdown("""
<style>
/* ── Layout ── */
.block-container{
    padding-top:5rem;
    padding-bottom:0.4rem;
}
[data-testid="stSidebar"]{display:none!important;}
[data-testid="collapsedControl"]{display:none!important;}
header[data-testid="stHeader"]{background:transparent!important;}
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

/* ── Nav buttons: taller touch targets ── */
#top-nav-marker + div .stButton>button,
#top-nav-marker ~ div .stButton>button{
    min-height:60px!important;
    font-size:1.3rem!important;
}

/* ── Random-page card ── */

/* ── Compact reel list ── */
.reel-info{
    padding:0;
    display:flex;
    flex-direction:column;
    justify-content:center;
    min-height:38px;
}
.reel-username{
    font-weight:750;
    font-size:0.96rem;
    white-space:nowrap;
    overflow:hidden;
    text-overflow:ellipsis;
    line-height:1.2;
    letter-spacing:-0.01em;
}
.reel-meta{
    color:rgba(255,255,255,0.42);
    font-size:0.62rem;
    margin-top:1px;
    letter-spacing:0.01em;
}
.reel-badge-fav{color:#f5a623;}
.reel-badge-del{opacity:0.45;}
/* ── Card container ── */
[data-testid="stVerticalBlockBorderWrapper"]{
    border-radius:16px!important;
    overflow:hidden;
}
[data-testid="stVerticalBlockBorderWrapper"]>div{
    padding:10px 14px!important;
    gap:0!important;
}

/* ── Inline action buttons (fav, del, more) ── */
.reel-action-btn .stButton>button{
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
.reel-action-btn .stButton>button:hover{
    background:rgba(255,255,255,0.12)!important;
}
.reel-action-btn .stButton>button[kind="primary"]{
    background:#FF4B4B!important;
    color:#fff!important;
    border:none!important;
}
.reel-action-btn .stButton>button[kind="primary"]:hover{
    background:#ff3333!important;
}
button[kind="secondary"]{
    background:rgba(255,255,255,0.03)!important;
    border:none!important;
}

@media(max-width:640px){
    .block-container{padding-left:0.5rem;padding-right:0.5rem;}
}
</style>
""", unsafe_allow_html=True)

# =========================
# HELPERS
# =========================

def ig_open_button(url: str, label: str = "🚀 Open in Instagram", full_width: bool = True):
    w = "100%" if full_width else "auto"
    js_url = json.dumps(url)
    components.html(f"""<style>
    *{{margin:0;padding:0;box-sizing:border-box;}}
    a{{display:flex;align-items:center;justify-content:center;width:{w};height:44px;
       border-radius:12px;font-size:0.95rem;font-weight:600;background:#FF4B4B;
       color:#fff;text-decoration:none;cursor:pointer;
       font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;}}
    a:active{{filter:brightness(.82);transform:scale(.97);}}
    </style>
    <a href="#" onclick="window.top.location.href={js_url};return false;">{label}</a>
    """, height=52, scrolling=False)

# =========================
# PERSISTENCE
# =========================

MARKERS_FILE = Path.home() / ".insta_vault_markers.json"

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
                if "insta_vault.json" in files:
                    data = json.loads(files["insta_vault.json"]["content"])
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
                json={"files": {"insta_vault.json": {"content": payload}}},
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
# LOAD DATA  (cached once)
# =========================

def parse_dates(series):
    parsed = pd.to_datetime(series, errors="coerce")
    mask = parsed.isna()
    if mask.any():
        parsed[mask] = pd.to_datetime(series[mask], format="%b %d, %Y %I:%M %p", errors="coerce")
    return parsed

@st.cache_data
def load_data():
    df = pd.read_csv("saved_posts.csv", encoding="utf-8")
    df = df[["post_url", "owner_username", "saved_date"]]
    df = df.dropna(subset=["post_url"]).drop_duplicates(subset=["post_url"])
    df["saved_date"] = parse_dates(df["saved_date"])
    df = df.dropna(subset=["saved_date"])
    df["id"] = range(1, len(df) + 1)
    return df

@st.cache_data
def get_username_index(_df):
    names = sorted(_df["owner_username"].dropna().unique().tolist())
    return names, [n.lower() for n in names]

@st.cache_data
def get_creator_counts(_df):
    return (
        _df.groupby("owner_username").size()
        .reset_index(name="saved_count")
        .sort_values("saved_count", ascending=False)
    )

@st.cache_data
def get_creator_saved_counts(_df):
    return _df.groupby("owner_username").size().reset_index(name="creator_saved_count")

df = load_data()
all_usernames, all_usernames_lower = get_username_index(df)

# =========================
# SESSION STATE
# =========================

if "favourites" not in st.session_state:
    favs, pdels = load_markers()
    st.session_state.favourites       = favs
    st.session_state.probably_deleted = pdels

if "excluded_users" not in st.session_state:
    st.session_state.excluded_users = []

# =========================
# NAVIGATION  (session-state, no query params)
# =========================

PAGES     = ["🎲 Random", "👤 Creators", "🕒 Timeline", "🔍 Search", "📊 Stats"]
NAV_ICONS = ["🎲",        "👤",          "🕒",          "🔍",        "📊"]

if "nav_page" not in st.session_state:
    st.session_state.nav_page = PAGES[0]

# Apply any pending programmatic navigation (e.g. from dialog username click)
if "_pending_nav" in st.session_state:
    st.session_state.nav_page = st.session_state.pop("_pending_nav")

page = st.session_state.nav_page

# =========================
# TOP NAV
# =========================

st.markdown('<div id="top-nav-marker"></div>', unsafe_allow_html=True)
_nav_cols = st.columns(5)
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
st.markdown("<hr style='margin:4px 0 12px;opacity:0.2'>", unsafe_allow_html=True)

# =========================
# DIALOG
# =========================

@st.dialog("📌 Post Details")
def post_dialog(row_dict):
    post_id = row_dict["id"]
    is_fav  = post_id in st.session_state.favourites
    is_del  = post_id in st.session_state.probably_deleted

    if st.button(
        f"👤 @{row_dict['owner_username']}",
        key=f"dlg_creator_{post_id}",
        use_container_width=True,
    ):
        st.session_state._pending_nav  = "👤 Creators"
        st.session_state.goto_creator  = row_dict["owner_username"]
        st.rerun()
    st.caption(f"📅 Saved {row_dict['saved_date'].strftime('%d %b %Y')}")
    ig_open_button(row_dict["post_url"])
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
        st.info("No posts match your filters.")
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

    st.caption(f"{total_posts:,} posts")
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

    for i, (_, row) in enumerate(page_df.iterrows()):
        post_id  = row["id"]
        is_fav   = post_id in favs
        is_del   = post_id in pdels

        uname         = row["owner_username"]
        uname_display = (uname[:22] + "…") if len(uname) > 23 else uname
        date_str      = row["saved_date"].strftime("%d %b %Y")

        if is_fav:
            badge_html = " <span class='reel-badge-fav'>★</span>"
        elif is_del:
            badge_html = " <span class='reel-badge-del'>🗑</span>"
        else:
            badge_html = ""

        with st.container(border=True):
            c_info, c_fav, c_del, c_more, c_open = st.columns([5, 2, 2, 2, 4], vertical_alignment="center")

            with c_info:
                st.markdown(
                    f"<div class='reel-info'>"
                    f"<div class='reel-username'>@{uname_display}{badge_html}</div>"
                    f"<div class='reel-meta'>{date_str}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            with c_fav:
                fav_active = post_id in favs
                st.markdown('<div class="reel-action-btn">', unsafe_allow_html=True)
                if st.button("★" if fav_active else "☆", key=f"fav_inline_{post_id}", use_container_width=True, type="primary" if fav_active else "secondary"):
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
                st.markdown('<div class="reel-action-btn">', unsafe_allow_html=True)
                if st.button("🗑", key=f"del_inline_{post_id}", use_container_width=True, type="primary" if del_active else "secondary"):
                    favs.discard(post_id)
                    if del_active:
                        pdels.discard(post_id)
                    else:
                        pdels.add(post_id)
                    save_markers(favs, pdels)
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            with c_more:
                st.markdown('<div class="reel-action-btn">', unsafe_allow_html=True)
                if st.button("⋮", key=f"menu_{key_prefix}_{post_id}", use_container_width=True):
                    post_dialog(row.to_dict())
                st.markdown('</div>', unsafe_allow_html=True)

            with c_open:
                js_url = json.dumps(row["post_url"])
                components.html(f"""<style>
                *{{margin:0;padding:0;box-sizing:border-box;}}
                a{{display:flex;align-items:center;justify-content:center;width:100%;height:38px;
                   border-radius:999px;font-size:0.85rem;font-weight:700;background:#FF4B4B;
                   color:#fff;text-decoration:none;cursor:pointer;
                   font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;}}
                a:active{{filter:brightness(.88);transform:scale(.97);}}
                </style>
                <a href="#" onclick="window.top.location.href={js_url};return false;">Open</a>
                """, height=46, scrolling=False)

    pagination_row("bot")

# =========================
# SEARCH INPUT HELPER
# =========================

def username_search_input(label, key, max_suggestions=10):
    selected_key = f"{key}_selected"
    input_key    = f"{key}_input"

    if st.session_state.get(selected_key):
        c_val, c_clr = st.columns([9, 1])
        with c_val:
            st.markdown(f"**{label}:** `@{st.session_state[selected_key]}`")
        with c_clr:
            if st.button("✕", key=f"{key}_clear"):
                st.session_state[selected_key] = ""
                st.rerun()
        return st.session_state[selected_key]

    query = st.text_input(label, key=input_key, placeholder="Type to search...")

    if query:
        q_lower = query.lower()
        matches = [
            all_usernames[i]
            for i, nl in enumerate(all_usernames_lower)
            if q_lower in nl
        ][:max_suggestions]

        if matches:
            choice = st.selectbox(
                "Suggestions",
                options=["— select —"] + matches,
                key=f"{key}_dropdown",
                label_visibility="collapsed",
            )
            if choice != "— select —":
                st.session_state[selected_key] = choice
                st.rerun()

    return query

# =========================
# RANDOM REEL PAGE
# =========================

if page == "🎲 Random":

    if "random_post" not in st.session_state:
        st.markdown("<div style='height:55vh'></div>", unsafe_allow_html=True)
        st.info("Tap **Open Random Saved Post** below to get started.")

    if "random_post" in st.session_state:
        st.markdown("<div style='height:30vh'></div>", unsafe_allow_html=True)
        post    = st.session_state.random_post
        post_id = post["id"]
        favs    = st.session_state.favourites
        pdels   = st.session_state.probably_deleted
        is_fav  = post_id in favs
        is_del  = post_id in pdels
        badge   = " ★" if is_fav else (" 🗑" if is_del else "")

        with st.container(border=True):
            col_name, col_goto = st.columns([9, 1])
            with col_name:
                st.markdown(f"**@{post['owner_username']}**{badge}")
            with col_goto:
                if st.button("👤", key="rnd_creator", help="Go to creator"):
                    st.session_state._pending_nav = "👤 Creators"
                    st.session_state.goto_creator = post["owner_username"]
                    st.rerun()
            st.caption(f"📅 {post['saved_date'].strftime('%d %b %Y')}")
            ig_open_button(post["post_url"])
            c_fav, c_del = st.columns(2)
            with c_fav:
                if st.button(
                    "★ Favourited" if is_fav else "☆ Favourite",
                    key="rnd_fav",
                    type="primary" if is_fav else "secondary",
                    use_container_width=True,
                ):
                    favs.discard(post_id)
                    pdels.discard(post_id)
                    if not is_fav:
                        favs.add(post_id)
                    save_markers(favs, pdels)
                    st.rerun()
            with c_del:
                if st.button(
                    "🗑 Marked" if is_del else "🗑 Prob. Deleted",
                    key="rnd_del",
                    type="primary" if is_del else "secondary",
                    use_container_width=True,
                ):
                    favs.discard(post_id)
                    pdels.discard(post_id)
                    if not is_del:
                        pdels.add(post_id)
                    save_markers(favs, pdels)
                    st.rerun()

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style="
            position:fixed;
            bottom:calc(18px + env(safe-area-inset-bottom));
            left:0;
            right:0;
            padding:0 14px;
            z-index:999;
        ">
        """,
        unsafe_allow_html=True,
    )
    if st.button("🎲 Open Random Saved Post", use_container_width=True, type="primary",
                 key="rnd_open"):
        st.session_state.random_post = df.sample(1).iloc[0].to_dict()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# CREATORS PAGE
# =========================

elif page == "👤 Creators":

    st.title("👤 Top Creators")

    creator_counts = get_creator_counts(df)

    goto_creator = st.session_state.pop("goto_creator", None)

    search_creator = st.text_input(
        "Search creator",
        value=goto_creator or "",
        placeholder="Type to filter...",
        key="creator_search_input",
    )

    if search_creator:
        creator_counts = creator_counts[
            creator_counts["owner_username"].str.contains(search_creator, case=False, na=False)
        ]

    st.caption(f"{len(creator_counts):,} creators")

    if creator_counts.empty:
        st.info("No creators match your search.")
        st.stop()

    options     = creator_counts["owner_username"].tolist()
    default_idx = options.index(goto_creator) if goto_creator and goto_creator in options else 0
    selected_creator = st.selectbox("Select Creator", options, index=default_idx)

    creator_info  = creator_counts[creator_counts["owner_username"] == selected_creator].iloc[0]
    creator_posts = df[df["owner_username"] == selected_creator].sort_values("saved_date", ascending=False)

    st.divider()
    st.markdown(f"### @{creator_info['owner_username']}")
    st.caption(f"{creator_info['saved_count']} saved posts")

    per_page_c = st.selectbox("Posts per page", [10, 25, 50, 100], index=1, key="creator_per_page")
    render_card_grid(creator_posts, per_page_c, "creator_page", "creator")

# =========================
# TIMELINE PAGE
# =========================

elif page == "🕒 Timeline":

    st.title("🕒 Timeline")

    creator_saved_counts = get_creator_saved_counts(df)

    c1, c2 = st.columns(2)
    with c1:
        sort_option = st.selectbox("Sort", ["Newest First", "Oldest First", "Most Saved Creator"])
    with c2:
        marker_filter = st.selectbox("Marker", ["All", "Favourites", "Probably Deleted", "Unmarked"])

    search_query = username_search_input("Search by username", key="timeline_search")

    with st.expander("⚙ More Filters"):
        min_date = df["saved_date"].min().date()
        max_date = df["saved_date"].max().date()
        start_date, end_date = st.date_input("Date Range", [min_date, max_date])

        per_page = st.selectbox("Posts per page", [10, 25, 50, 100], index=1)

        st.markdown("**🚫 Exclude Creators**")
        exclude_query = username_search_input("Exclude username", key="exclude_search")
        if exclude_query and exclude_query not in st.session_state.excluded_users:
            if st.button(f"🚫 Exclude @{exclude_query}", use_container_width=True):
                st.session_state.excluded_users.append(exclude_query)
                st.session_state["exclude_search_selected"] = ""
                st.rerun()
        if st.session_state.excluded_users:
            for uname in list(st.session_state.excluded_users):
                c_u, c_rm = st.columns([5, 1])
                with c_u:
                    st.caption(f"🚫 @{uname}")
                with c_rm:
                    if st.button("✕", key=f"rm_{uname}"):
                        st.session_state.excluded_users.remove(uname)
                        st.rerun()
        else:
            st.caption("None excluded.")

    filter_sig = (sort_option, marker_filter, search_query, start_date, end_date, per_page,
                  tuple(st.session_state.excluded_users))
    if st.session_state.get("tl_filter_sig") != filter_sig:
        st.session_state["tl_filter_sig"] = filter_sig
        st.session_state["timeline_page"]  = 0

    mask = (
        (df["saved_date"].dt.date >= start_date) &
        (df["saved_date"].dt.date <= end_date)
    )
    if search_query:
        mask &= df["owner_username"].str.contains(search_query, case=False, na=False)
    if st.session_state.excluded_users:
        mask &= ~df["owner_username"].isin(st.session_state.excluded_users)

    favs  = st.session_state.favourites
    pdels = st.session_state.probably_deleted
    if marker_filter == "Favourites":
        mask &= df["id"].isin(favs)
    elif marker_filter == "Probably Deleted":
        mask &= df["id"].isin(pdels)
    elif marker_filter == "Unmarked":
        mask &= ~df["id"].isin(favs | pdels)

    fdf = df[mask]

    if sort_option == "Newest First":
        fdf = fdf.sort_values("saved_date", ascending=False)
    elif sort_option == "Oldest First":
        fdf = fdf.sort_values("saved_date", ascending=True)
    else:
        fdf = fdf.merge(creator_saved_counts, on="owner_username", how="left")
        fdf = fdf.sort_values(["creator_saved_count", "saved_date"], ascending=[False, False])

    render_card_grid(fdf, per_page, "timeline_page", "timeline")

# =========================
# SEARCH PAGE
# =========================

elif page == "🔍 Search":

    st.title("🔍 Search")

    query = username_search_input("Search by username", key="search_page")

    if query:
        results    = df[df["owner_username"].str.contains(query, case=False, na=False)]
        per_page_s = st.selectbox("Posts per page", [10, 25, 50, 100], index=1, key="search_per_page")

        search_sig = (query, per_page_s)
        if st.session_state.get("search_filter_sig") != search_sig:
            st.session_state["search_filter_sig"] = search_sig
            st.session_state["search_page_num"]   = 0

        render_card_grid(results, per_page_s, "search_page_num", "search")

# =========================
# STATS PAGE
# =========================

elif page == "📊 Stats":

    st.title("📊 Vault Statistics")

    vc = df["owner_username"].value_counts()

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Total Posts",    f"{len(df):,}")
        st.metric("Total Creators", f"{df['owner_username'].nunique():,}")
    with c2:
        st.metric("Top Creator",       vc.idxmax())
        st.metric("Top Creator Saves", f"{vc.max():,}")

    st.divider()
    oldest, newest = df["saved_date"].min(), df["saved_date"].max()
    st.caption(f"📅 {oldest.strftime('%d %b %Y')} → {newest.strftime('%d %b %Y')}")

    st.divider()
    st.subheader("🏆 Top 25 Creators")
    st.dataframe(vc.head(25), use_container_width=True)

    st.divider()
    st.subheader("🔖 Markers")
    st.caption(
        f"★ Favourites: {len(st.session_state.favourites):,}  ·  "
        f"🗑 Prob. Deleted: {len(st.session_state.probably_deleted):,}"
    )
    with st.expander("Clear markers"):
        if st.button("Clear Favourites", use_container_width=True):
            st.session_state.favourites = set()
            save_markers(st.session_state.favourites, st.session_state.probably_deleted)
            st.rerun()
        if st.button("Clear Prob. Deleted", use_container_width=True):
            st.session_state.probably_deleted = set()
            save_markers(st.session_state.favourites, st.session_state.probably_deleted)
            st.rerun()

