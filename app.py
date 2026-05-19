import streamlit as st
import pandas as pd
import json
from pathlib import Path

# Stored in the home directory so it survives git redeployments on Streamlit Cloud
CHECKED_FILE = Path.home() / ".insta_vault_checked.json"

def load_checked():
    if CHECKED_FILE.exists():
        try:
            return set(json.loads(CHECKED_FILE.read_text(encoding="utf-8")))
        except Exception:
            return set()
    return set()

def save_checked(checked: set):
    CHECKED_FILE.write_text(
        json.dumps(list(checked)),
        encoding="utf-8"
    )

# =========================
# PAGE CONFIG
# =========================

st.set_page_config(
    page_title="📸 Insta Vault",
    page_icon="📸",
    layout="wide"
)

# =========================
# LOAD DATA
# =========================

def parse_dates(series):
    # Try standard parsing first, then the "Jan 14, 2023 1:33 pm" format
    parsed = pd.to_datetime(series, errors="coerce")
    mask = parsed.isna()
    if mask.any():
        parsed[mask] = pd.to_datetime(
            series[mask], format="%b %d, %Y %I:%M %p", errors="coerce"
        )
    return parsed

@st.cache_data
def load_data():
    df = pd.read_csv("saved_posts.csv", encoding="utf-8")

    required_columns = ["post_url", "owner_username", "saved_date"]
    df = df[required_columns]
    df = df.dropna(subset=["post_url"])
    df = df.drop_duplicates(subset=["post_url"])
    df["saved_date"] = parse_dates(df["saved_date"])
    df = df.dropna(subset=["saved_date"])
    df["id"] = range(1, len(df) + 1)

    return df

df = load_data()

# =========================
# CHECKED POSTS STATE
# =========================

if "checked_posts" not in st.session_state:
    st.session_state["checked_posts"] = load_checked()

if "excluded_users" not in st.session_state:
    st.session_state["excluded_users"] = []

def toggle_check(post_id, checked):
    if checked:
        st.session_state["checked_posts"].add(post_id)
    else:
        st.session_state["checked_posts"].discard(post_id)
    save_checked(st.session_state["checked_posts"])
    st.rerun()

def render_post_card(row, key_prefix):
    post_id = row["id"]
    is_checked = post_id in st.session_state["checked_posts"]

    with st.container(border=True):
        col_check, col_info = st.columns([1, 11])

        with col_check:
            checked = st.checkbox(
                "",
                value=is_checked,
                key=f"chk_{key_prefix}_{post_id}"
            )
            if checked != is_checked:
                toggle_check(post_id, checked)

        with col_info:
            st.write(f"👤 @{row['owner_username']}")
            st.write(f"📅 {row['saved_date'].strftime('%d %b %Y')}")
            st.link_button(
                "🚀 Open Post",
                row["post_url"],
                use_container_width=True
            )

# =========================
# SIDEBAR
# =========================

st.sidebar.title("📸 Insta Vault")

page = st.sidebar.radio(
    "Navigation",
    [
        "🎲 Random Reel",
        "👤 Creators",
        "🕒 Timeline",
        "🔍 Search",
        "📊 Stats"
    ]
)

st.sidebar.write(f"✅ Checked: {len(st.session_state['checked_posts']):,}")

if st.sidebar.button("Clear All Checks"):
    st.session_state["checked_posts"] = set()
    save_checked(st.session_state["checked_posts"])
    st.rerun()

# =========================
# RANDOM REEL PAGE
# =========================

if page == "🎲 Random Reel":

    st.title("🎲 Random Reel")

    if st.button("🎲 Open Random Saved Post", use_container_width=True):
        st.session_state["random_post"] = df.sample(1).iloc[0].to_dict()

    if "random_post" in st.session_state:
        post = st.session_state["random_post"]
        post_id = post["id"]
        is_checked = post_id in st.session_state["checked_posts"]

        with st.container(border=True):
            col_check, col_info = st.columns([1, 11])

            with col_check:
                checked = st.checkbox(
                    "",
                    value=is_checked,
                    key=f"chk_random_{post_id}"
                )
                if checked != is_checked:
                    toggle_check(post_id, checked)

            with col_info:
                st.subheader(f"@{post['owner_username']}")
                st.write(f"📅 Saved Date: {post['saved_date'].strftime('%d %b %Y')}")
                st.link_button(
                    "🚀 Open in Instagram",
                    post["post_url"],
                    use_container_width=True
                )
                st.code(post["post_url"])

# =========================
# CREATORS PAGE
# =========================

elif page == "👤 Creators":

    st.title("👤 Top Creators")

    creator_counts = (
        df.groupby("owner_username")
        .size()
        .reset_index(name="saved_count")
        .sort_values(by="saved_count", ascending=False)
    )

    search_creator = st.text_input("Search creator")

    if search_creator:
        creator_counts = creator_counts[
            creator_counts["owner_username"]
            .str.contains(search_creator, case=False, na=False)
        ]

    st.write(f"Total creators: {len(creator_counts):,}")

    selected_creator = st.selectbox(
        "Select Creator",
        creator_counts["owner_username"].tolist()
    )

    creator_info = creator_counts[
        creator_counts["owner_username"] == selected_creator
    ].iloc[0]

    st.subheader(f"@{creator_info['owner_username']}")
    st.write(f"Saved Posts: {creator_info['saved_count']}")

    creator_posts = df[
        df["owner_username"] == selected_creator
    ].sort_values(by="saved_date", ascending=False)

    st.write(f"Posts from creator: {len(creator_posts):,}")

    for _, row in creator_posts.head(100).iterrows():
        render_post_card(row, "creator")

# =========================
# TIMELINE PAGE
# =========================

elif page == "🕒 Timeline":

    st.title("🕒 Timeline")

    creator_saved_counts = (
        df.groupby("owner_username")
        .size()
        .reset_index(name="creator_saved_count")
    )

    # --- Filters ---
    col_f1, col_f2 = st.columns(2)

    with col_f1:
        sort_option = st.selectbox(
            "Sort Order",
            ["Newest First", "Oldest First", "Most Saved Creator"]
        )

    with col_f2:
        check_filter = st.selectbox(
            "Filter by Checked",
            ["All", "Checked Only", "Unchecked Only"]
        )

    search_query = st.text_input("Search by username")

    # --- Exclude usernames ---
    with st.expander("🚫 Exclude Creators"):
        exclude_input = st.text_input(
            "Type a username to exclude and press Enter",
            key="exclude_input"
        )
        if exclude_input and exclude_input not in st.session_state["excluded_users"]:
            if st.button("Add to exclude list"):
                st.session_state["excluded_users"].append(exclude_input)
                st.rerun()

        if st.session_state["excluded_users"]:
            st.write("Currently excluded:")
            for uname in list(st.session_state["excluded_users"]):
                col_u, col_rm = st.columns([5, 1])
                with col_u:
                    st.write(f"🚫 @{uname}")
                with col_rm:
                    if st.button("✕", key=f"rm_excl_{uname}"):
                        st.session_state["excluded_users"].remove(uname)
                        st.rerun()
        else:
            st.write("No creators excluded.")

    min_date = df["saved_date"].min().date()
    max_date = df["saved_date"].max().date()

    start_date, end_date = st.date_input(
        "Filter Date Range",
        [min_date, max_date]
    )

    per_page = st.selectbox("Posts per page", [10, 25, 50, 100], index=1)

    # Reset to page 0 when any filter changes
    filter_sig = (
        sort_option, check_filter, search_query,
        start_date, end_date, per_page,
        tuple(st.session_state["excluded_users"])
    )
    if st.session_state.get("timeline_filter_sig") != filter_sig:
        st.session_state["timeline_filter_sig"] = filter_sig
        st.session_state["timeline_page"] = 0

    # --- Build filtered df ---
    filtered_df = df.copy()

    filtered_df = filtered_df[
        (filtered_df["saved_date"].dt.date >= start_date)
        & (filtered_df["saved_date"].dt.date <= end_date)
    ]

    if search_query:
        filtered_df = filtered_df[
            filtered_df["owner_username"]
            .str.contains(search_query, case=False, na=False)
        ]

    if st.session_state["excluded_users"]:
        filtered_df = filtered_df[
            ~filtered_df["owner_username"].isin(st.session_state["excluded_users"])
        ]

    if check_filter == "Checked Only":
        filtered_df = filtered_df[
            filtered_df["id"].isin(st.session_state["checked_posts"])
        ]
    elif check_filter == "Unchecked Only":
        filtered_df = filtered_df[
            ~filtered_df["id"].isin(st.session_state["checked_posts"])
        ]

    if sort_option == "Newest First":
        filtered_df = filtered_df.sort_values(by="saved_date", ascending=False)
    elif sort_option == "Oldest First":
        filtered_df = filtered_df.sort_values(by="saved_date", ascending=True)
    else:  # Most Saved Creator
        filtered_df = filtered_df.merge(creator_saved_counts, on="owner_username", how="left")
        filtered_df = filtered_df.sort_values(
            by=["creator_saved_count", "saved_date"],
            ascending=[False, False]
        )

    # --- Pagination ---
    total_posts = len(filtered_df)
    total_pages = max(1, -(-total_posts // per_page))  # ceiling division
    current_page = st.session_state.get("timeline_page", 0)
    current_page = min(current_page, total_pages - 1)
    st.session_state["timeline_page"] = current_page

    start_idx = current_page * per_page
    page_df = filtered_df.iloc[start_idx : start_idx + per_page]

    st.write(f"Posts found: {total_posts:,}  |  Page {current_page + 1} of {total_pages:,}")

    col_prev, col_next = st.columns(2)
    with col_prev:
        if st.button("◀ Previous", disabled=(current_page == 0), use_container_width=True):
            st.session_state["timeline_page"] -= 1
            st.rerun()
    with col_next:
        if st.button("Next ▶", disabled=(current_page >= total_pages - 1), use_container_width=True):
            st.session_state["timeline_page"] += 1
            st.rerun()

    for _, row in page_df.iterrows():
        render_post_card(row, "timeline")

    col_prev2, col_next2 = st.columns(2)
    with col_prev2:
        if st.button("◀ Previous ", disabled=(current_page == 0), use_container_width=True):
            st.session_state["timeline_page"] -= 1
            st.rerun()
    with col_next2:
        if st.button("Next ▶ ", disabled=(current_page >= total_pages - 1), use_container_width=True):
            st.session_state["timeline_page"] += 1
            st.rerun()

# =========================
# SEARCH PAGE
# =========================

elif page == "🔍 Search":

    st.title("🔍 Search")

    query = st.text_input("Search by username")

    if query:
        results = df[
            df["owner_username"]
            .str.contains(query, case=False, na=False)
        ]

        st.write(f"Results found: {len(results):,}")

        for _, row in results.head(200).iterrows():
            render_post_card(row, "search")

# =========================
# STATS PAGE
# =========================

elif page == "📊 Stats":

    st.title("📊 Vault Statistics")

    total_posts = len(df)
    total_creators = df["owner_username"].nunique()
    oldest_post = df["saved_date"].min()
    newest_post = df["saved_date"].max()
    top_creator = df["owner_username"].value_counts().idxmax()
    top_creator_count = df["owner_username"].value_counts().max()

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Total Saved Posts", f"{total_posts:,}")
        st.metric("Total Creators", f"{total_creators:,}")

    with col2:
        st.metric("Top Creator", top_creator)
        st.metric("Top Creator Saves", f"{top_creator_count:,}")

    st.write("---")
    st.write(f"📅 Oldest Save: {oldest_post.strftime('%d %b %Y')}")
    st.write(f"📅 Newest Save: {newest_post.strftime('%d %b %Y')}")
    st.write("---")

    st.subheader("🏆 Top 25 Creators")
    st.dataframe(df["owner_username"].value_counts().head(25))
