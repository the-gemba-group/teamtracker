import streamlit as st
import base64

def image_to_base64(image_path):
    """Convert a local image to a base64‑encoded string."""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Path to your local banner image
banner_path = "images/Gemba.png"

def login_page():
    # --- Inject CSS for styling the login page ---
    st.markdown(
        """
        <style>
        .stButton>button {
            background-color: #F0145A !important;
            color: #ffffff !important;
            border-radius: 5px !important;
            width: 100% !important;
            height: 40px !important;
            font-size: 16px !important;
            font-weight: bold !important;
            border: none !important;
            transition: background-color 0.2s ease-in-out;
        }
        .stButton>button:hover {
            background-color: #F6729B !important;
            color: #000000 !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # --- Display banner image and heading ---
    banner_b64 = image_to_base64(banner_path)
    st.markdown(
        f"""
        <div style="text-align: center; margin-bottom: 10px;">
            <img src="data:image/png;base64,{banner_b64}"
                 alt="Banner" style="width: 100%; max-width: 300px;">
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown("<h4 style='text-align: center;'>Team Tracker PRO</h4>", unsafe_allow_html=True)

    # --- Login form inputs ---
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")

    # --- Authenticate on button press ---
    if st.button("Authenticate"):
        # Allowed credentials
        valid = (
            (username == "markz" and password == "@gemba#1") or
            (username == "o"     and password == "1")
        )
        if valid:
            st.session_state.authenticated = True
            # Immediately rerun so index.py picks up authenticated=True
            st.rerun()
        else:
            st.error("Invalid credentials")
