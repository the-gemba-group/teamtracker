import streamlit as st
import time
from streamlit_autorefresh import st_autorefresh

# -----------------------------------------------------------------------------
# Page Config (must be first Streamlit call)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Team Tracker", layout="wide", initial_sidebar_state="collapsed")

# -----------------------------------------------------------------------------
# CSS to reduce top padding/margins
# -----------------------------------------------------------------------------
st.markdown("""
<style>
.block-container {
    padding-top: 1.5rem !important;
    margin-top: 0 !important;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Custom Sidebar Styling + Navigation
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Global font */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
    }
    /* Sidebar background */
    [data-testid="stSidebar"] {
        background-color: #AAA8A8!important;
        color: #ffffff !important;
        padding-top: 10px !important;
    }
    /* Button styling */
    .stButton>button {
        background-color: #F0145A !important;
        color: #ffffff !important;
        border-radius: 5px !important;
        width: 90% !important;
        height: 40px !important;
        font-size: 16px !important;
        margin: 0 auto 10px auto !important;
        display: block !important;
        border: none !important;
        transition: background-color 0.2s ease-in-out, color 0.2s ease-in-out;
    }
    .stButton>button:hover {
        background-color: #F6729B !important;
        color: #000000 !important;
    }
    /* Sidebar headings */
    .sidebar-title {
        text-align: center;
        font-size: 20px;
        color: #000000;
        margin: 10px 0;
    }
    .powered-by {
        text-align: center;
        font-size: 12px;
        color: #000000;
        margin-top: 20px;
    }
    .stDownloadButton>button {
    background-color: #F0145A !important;
    color: #ffffff !important;
    border-radius: 5px !important;
    width: 90% !important;
    height: 40px !important;
    font-size: 16px !important;
    margin: 0 auto !important;
    display: block !important;
    border: none !important;
    transition: background-color 0.2s ease-in-out, color 0.2s ease-in-out;
}
.stDownloadButton>button:hover {
    background-color: #F6729B!important;
    color: #000000 !important;
    </style>
    """,
    unsafe_allow_html=True
)

def customize_sidebar():
    with st.sidebar:
        # Logo
        st.image("images/Gemba.png", use_container_width=True)
        # Title
        st.markdown("<div class='sidebar-title'>TIME TRACKER PRO</div>", unsafe_allow_html=True)
        # Navigation buttons
        if st.button("Settings", key="nav_settings"):
            st.session_state.page = "Settings"
        if st.button("Match", key="nav_match"):
            st.session_state.page = "Match"
        # Footer
        st.markdown("<div class='powered-by'>Powered by Gemba</div>", unsafe_allow_html=True)

# Call it once (so that session_state.page exists)
if "page" not in st.session_state:
    st.session_state.page = "Settings"
customize_sidebar()


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------
def format_elapsed_time(seconds):
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"

def get_color(position):
    if position == "Forward":   return ("green","white")
    if position == "Midfield":  return ("blue","white")
    if position == "Defence":   return ("purple","white")
    if position == "Off":       return ("black","white")
    return ("lightgrey","black")

def accumulate_time():
    now = time.time()
    delta = now - st.session_state.last_update_time
    for p, pos in st.session_state.current_positions.items():
        if pos != "Off":
            st.session_state.position_time[p][pos] += delta
    st.session_state.last_update_time = now

def commit_position_change(player):
    now = time.time()

    # 1) Accumulate live time if quarter is running
    if st.session_state.quarter_running:
        accumulate_time()

    # 2) Determine old vs new
    old_pos = st.session_state.current_positions.get(player, "Off")
    mapping = {"FWD":"Forward", "MID":"Midfield", "DEF":"Defence", "Off":"Off"}
    new_val = st.session_state.get(f"radio_{player}", "Off")
    new_pos = mapping[new_val]

    # 3) Only bump rotations on Off → On (not On→On or On→Off)
    if st.session_state.quarter_running and old_pos == "Off" and new_pos != "Off":
        st.session_state.rotations[player] = st.session_state.rotations.get(player, 0) + 1

    # 4) Update position
    st.session_state.current_positions[player] = new_pos

    # 5) Reset last‑tick so we don’t double‑count
    st.session_state.last_update_time = now
    st.session_state.alert_msg = ""

# -----------------------------------------------------------------------------
# Settings Page
# -----------------------------------------------------------------------------
def show_settings():
    st.header("Settings")
    st.write("Enter up to 25 players (one per line).")
    existing = "\n".join(st.session_state.players)
    player_input = st.text_area("Player Names", value=existing, height=200)

    if st.button("Save Settings"):
        names = [n.strip() for n in player_input.split("\n") if n.strip()][:25]
        st.session_state.players = names
        st.session_state.position_time = {n: {"Forward": 0, "Midfield": 0, "Defence": 0} for n in names}
        st.session_state.current_positions = {n: "Off" for n in names}
        st.session_state.rotations = {n: 0 for n in names}
        st.session_state.quarter_reports = {}
        st.session_state.quarter_durations = {}
        st.session_state.alert_msg = ""
        st.success("Settings saved!")

    st.write("Current players:")
    for i, n in enumerate(st.session_state.players, 1):
        st.write(f"{i}. {n}")

# -----------------------------------------------------------------------------
# Match Page (with embedded final report + quarter lengths)
# -----------------------------------------------------------------------------
def show_match():
    # --- 0) While quarter is running, accumulate and auto-refresh ---
    if st.session_state.quarter_running:
        accumulate_time()
        st_autorefresh(interval=1000, limit=None, key="clock_autorefresh")

    now = time.time()

        # --- 1) Header row: custom HTML (no extra top margin) ---
    if st.session_state.quarter_running:
        elapsed = now - st.session_state.quarter_start_time
        mm, ss = divmod(int(elapsed), 60)
        timer_str = f"{mm:02d}:{ss:02d}"
    else:
        timer_str = "00:00"

    st.markdown(f"""
    <div style="
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 0 0 1rem 0;  /* top=0, bottom=1rem */
        padding: 0;
    ">
        <h1 style="margin: 0; padding: 0;">Time on Ground</h1>
        <div style="font-size:3.5rem; line-height:0;">{timer_str}</div>
    </div>
    """, unsafe_allow_html=True)

        # --- 2) Control row: alert + quarter label + start/end/end‑match button ---
    control_cols = st.columns(4)
    # (2a) Alert
    with control_cols[2]:
        if st.session_state.alert_msg:
            st.markdown(
                "<div style='text-align:right;color:green;margin-right:1rem;'>"
                f"{st.session_state.alert_msg}</div>",
                unsafe_allow_html=True
            )
            st.session_state.alert_msg = ""

    # (2b) Quarter label + dynamic button
    with control_cols[3]:
        # Quarter label on the left
        label_col, btn_col = st.columns([1,1])
        with label_col:
            st.markdown(
                f"<div style='display:flex; align-items:center; height:100%; margin-left:2rem;'>"
                f"<strong>Quarter {st.session_state.quarter_number}</strong>"
                f"</div>",
                unsafe_allow_html=True
            )

        # Button / Finished message on the right
        with btn_col:
            # If the match is already finished
            if st.session_state.match_finished:
                st.markdown(
                    "<div style='text-align:center; color:green;'>"
                    "Match Finished</div>",
                    unsafe_allow_html=True
                )

            # Otherwise, if not running, show Start Quarter
            elif not st.session_state.quarter_running:
                if st.button("Start Quarter", key="start_btn"):
                    now = time.time()
                    st.session_state.quarter_running = True
                    st.session_state.quarter_start_time = now
                    st.session_state.last_update_time = now

                    # Snapshot for possible quarter restart
                    st.session_state.pre_quarter_position_time = {
                        p: st.session_state.position_time[p].copy()
                        for p in st.session_state.players
                    }
                    # Bump rotations for those already on
                    for p, pos in st.session_state.current_positions.items():
                        if pos != "Off":
                            st.session_state.rotations[p] = st.session_state.rotations.get(p, 0) + 1

                    st.session_state.alert_msg = f"Quarter {st.session_state.quarter_number} started!"
                    st.rerun()

            # If running, show End Quarter or End Match
            else:
                # Decide label based on quarter number
                is_last = (st.session_state.quarter_number == 4)
                btn_label = "End Match" if is_last else "End Quarter"

                if st.button(btn_label, key="end_btn"):
                    now = time.time()
                    accumulate_time()

                    # Record this quarter's duration
                    dur = now - st.session_state.quarter_start_time
                    st.session_state.quarter_durations[st.session_state.quarter_number] = dur

                    # Snapshot end-of-quarter times
                    qr = st.session_state.quarter_reports
                    qr[st.session_state.quarter_number] = {
                        p: st.session_state.position_time[p].copy()
                        for p in st.session_state.players
                    }
                    st.session_state.quarter_reports = qr

                    # End the quarter
                    st.session_state.quarter_running = False

                    if is_last:
                        # Final quarter ended → finish match
                        st.session_state.match_finished = True
                        st.session_state.alert_msg = "Match Finished!"
                    else:
                        st.session_state.alert_msg = f"Quarter {st.session_state.quarter_number} ended."
                        st.session_state.quarter_number += 1

                    st.rerun()

    # --- 3) Compute total match time so far ---
    # Sum durations of all completed quarters:
    total_match_secs = sum(st.session_state.quarter_durations.get(q, 0.0)
                        for q in range(1, st.session_state.quarter_number))

    # If the quarter is running, add the live elapsed:
    if st.session_state.quarter_running:
        total_match_secs += now - st.session_state.quarter_start_time


    # --- 4) Player columns by position category (Off first) ---
    short = {"Forward":"FWD","Midfield":"MID","Defence":"DEF","Off":"Off"}
    choices = ["Off","FWD","MID","DEF"]
    to_internal = {"FWD":"Forward","MID":"Midfield","DEF":"Defence","Off":"Off"}

    # helper to compute % time on ground
    def pct_for(p):
        pd = st.session_state.position_time[p]
        total = pd["Forward"] + pd["Midfield"] + pd["Defence"]
        return (total / total_match_secs * 100) if total_match_secs > 0 else 0

    cols = st.columns(4)
    new_pos = {}

    for col_idx, category in enumerate(["Off","Defence","Midfield","Forward"]):
        col = cols[col_idx]

        # filter players in this category
        players_in_cat = [
            p for p in st.session_state.players
            if st.session_state.current_positions.get(p, "Off") == category
        ]

        # sort: Off ascending, others descending
        if category == "Off":
            players_in_cat.sort(key=pct_for)  # least→most
        else:
            players_in_cat.sort(key=pct_for, reverse=True)  # most→least

        # render each player
        for p in players_in_cat:
            pct = pct_for(p)
            bg, fg = get_color(category)
            # info line
            col.markdown(
                f"<div style='font-weight:bold; font-size:20px; margin-bottom:0.25rem;'>"
                f"{p} | {pct:.0f}% | "
                f"<span style='background-color:{bg}; color:{fg}; padding:4px 12px; "
                f"border:1px solid {bg}; border-radius:4px;'>{short[category]}</span>"
                f"</div>",
                unsafe_allow_html=True
            )
            # radio button
            cur = short[st.session_state.current_positions[p]]
            sel = col.radio(
                label="",
                options=choices,
                index=choices.index(cur),
                key=f"radio_{p}",
                horizontal=True,
                on_change=commit_position_change,
                args=(p,),
            )
            new_pos[p] = to_internal[sel]

    st.session_state.current_positions.update(new_pos)

    # --- 5) Final Match Report (live, sorted by Pct(Game) desc) ---
    st.markdown("---")
    st.subheader("Report")
    st.markdown(
    "<div style='margin-bottom:0.5rem; color:gray;'>"
    "Sorted by Total Player Match % (Highest → Lowest)"
    "</div>",
    unsafe_allow_html=True)
    # Build a list of (pct_value, row_dict) tuples
    report_data = []
    total_game_time = total_match_secs
    for p in st.session_state.players:
        pd = st.session_state.position_time[p]
        fwd, mid, dfc = pd["Forward"], pd["Midfield"], pd["Defence"]
        tot = fwd + mid + dfc
        pct_game = (tot / total_match_secs * 100) if total_match_secs > 0 else 0
        row = {
            "Player":      p,
            "FWD":         format_elapsed_time(fwd),
            "MID":         format_elapsed_time(mid),
            "DEF":         format_elapsed_time(dfc),
            "Total":       format_elapsed_time(tot),
            "Pct (Game)":  f"{pct_game:.0f}%",
            "Rotations":   st.session_state.rotations.get(p, 0)
        }
        report_data.append((pct_game, row))

    # Sort by pct_game descending
    report_data.sort(key=lambda x: x[0], reverse=True)

    # Extract just the row dicts in sorted order
    sorted_rows = [row for _, row in report_data]

    st.table(sorted_rows)

        # --- 6) Quarter Lengths Summary (dynamic) ---
    st.subheader("Quarter Lengths")
    qlens = {}
    total = 0.0
    now = time.time()

    for q in range(1, 5):
        if q < st.session_state.quarter_number:
            # already completed
            dur = st.session_state.quarter_durations.get(q, 0.0)
        elif q == st.session_state.quarter_number and st.session_state.quarter_running:
            # currently running quarter
            dur = now - st.session_state.quarter_start_time
        else:
            # future quarter not started
            dur = 0.0

        total += dur
        m, s = divmod(int(dur), 60)
        qlens[f"Q{q}"] = f"{m:02d}:{s:02d}"

    # grand total so far (including live quarter)
    m, s = divmod(int(total), 60)
    qlens["Total"] = f"{m:02d}:{s:02d}"

    st.table([qlens])

    # -------------------------------------------------------------------------
    # Restart Match button
    # -------------------------------------------------------------------------
    st.markdown("---")
    col1, col2, col3 = st.columns([1,1,1])

    # Restart Match
    with col1:
        if st.button("Restart Match", key="restart_btn"):
            names = st.session_state.players
            # Reset match state
            st.session_state.quarter_running    = False
            st.session_state.quarter_number     = 1
            st.session_state.quarter_start_time = 0.0
            st.session_state.last_update_time   = 0.0
            st.session_state.alert_msg          = ""
            # Reset per-player data
            st.session_state.position_time      = {n:{"Forward":0,"Midfield":0,"Defence":0} for n in names}
            st.session_state.current_positions  = {n:"Off" for n in names}
            st.session_state.rotations          = {n:0 for n in names}
            # Clear quarter summaries
            st.session_state.quarter_reports    = {}
            st.session_state.quarter_durations  = {}
            st.success("Match reset! Player list preserved.")
            st.rerun()

    # 2) Restart Current Quarter Only
    with col2:
        if st.button("Restart Quarter", key="restart_qtr_btn"):
            now = time.time()
            qn = st.session_state.quarter_number

            # 1) Restore each player's time to the snapshot taken at quarter start
            pre = st.session_state.get("pre_quarter_position_time", {})
            for p in st.session_state.players:
                if p in pre:
                    st.session_state.position_time[p] = pre[p].copy()

            # 2) Stop the quarter clock
            st.session_state.quarter_running    = False
            st.session_state.quarter_start_time = 0.0
            st.session_state.last_update_time   = 0.0

            # 3) Clear any recorded duration/report for this quarter
            st.session_state.quarter_durations.pop(qn, None)
            st.session_state.quarter_reports.pop(qn, None)

            # 4) Let the user know and force them to press Start again
            st.session_state.alert_msg = f"Quarter {qn} reset. Press Start to begin."
            st.rerun()

    # -------------------------------------------------------------------------
        # Export Final Report to PDF
    # -------------------------------------------------------------------------
    with col3:
        try:
            from io import BytesIO
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet

            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []
            styles = getSampleStyleSheet()

            # Title
            elements.append(Paragraph("Time on Ground Match Report", styles["Heading2"]))
            elements.append(Spacer(1, 12))

            # Table data (using your sorted_rows list)
            data = [list(sorted_rows[0].keys())] + [list(r.values()) for r in sorted_rows]
            tbl = Table(data, repeatRows=1)
            tbl.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
                ("GRID",        (0,0), (-1,-1), 0.5, colors.grey),
                ("ALIGN",       (0,0), (-1,-1), "CENTER"),
                ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
            ]))
            elements.append(tbl)

            doc.build(elements)
            pdf_bytes = buffer.getvalue()

            st.download_button(
                label="Export Final Report PDF",
                data=pdf_bytes,
                file_name="final_report.pdf",
                mime="application/pdf",
                key="export_pdf"
            )
        except ModuleNotFoundError:
            st.error("Unable to export!")

# -----------------------------------------------------------------------------
# Main App
# -----------------------------------------------------------------------------
def main_app():
    defaults = {
        # Pre‑populate with 4 players
        "players": [
            "Player Name 1",
            "Player Name 2",
            "Player Name 3",
            "Player Name 4",
        ],
        "position_time": {},
        "current_positions": {},
        "quarter_running": False,
        "quarter_number": 1,
        "quarter_start_time": 0.0,
        "last_update_time": 0.0,
        "rotations": {},
        "quarter_reports": {},
        "quarter_durations": {},
        "alert_msg": "",
        "match_finished": False
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # --- Seed per-player dicts for the default names ---
    for p in st.session_state.players:
        if p not in st.session_state.position_time:
            st.session_state.position_time[p] = {"Forward":0, "Midfield":0, "Defence":0}
        if p not in st.session_state.current_positions:
            st.session_state.current_positions[p] = "Off"
        if p not in st.session_state.rotations:
            st.session_state.rotations[p] = 0
    # Ensure the summary dicts exist
    if "quarter_reports" not in st.session_state:
        st.session_state.quarter_reports = {}
    if "quarter_durations" not in st.session_state:
        st.session_state.quarter_durations = {}

    # Sidebar page state (set once)
    if "page" not in st.session_state:
        st.session_state.page = "Settings"

    page = st.session_state.page

    if page == "Settings":
        show_settings()
    else:
        show_match()

if __name__ == "__main__":
    main_app()
