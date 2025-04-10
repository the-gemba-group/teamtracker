import streamlit as st
from login import login_page
from teamtracker import main_app

# -----------------------------------------------------------------------------
# Page Config (must be the first Streamlit call in your app)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Team Tracker PRO",
    page_icon="images/Gemba.png",   # Path relative to your app root
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -----------------------------------------------------------------------------
# Authentication state initialization
# -----------------------------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# -----------------------------------------------------------------------------
# Route to login or main app based on authentication
# -----------------------------------------------------------------------------
if not st.session_state.authenticated:
    login_page()
else:
    main_app()
