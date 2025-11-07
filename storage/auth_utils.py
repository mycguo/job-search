"""
Authentication utilities for Streamlit.

Handles authentication safely across different Streamlit versions and deployment environments.
"""

try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False


def is_user_logged_in() -> bool:
    """
    Safely check if user is logged in.
    
    Returns:
        True if user is logged in, False otherwise.
        In environments where st.user.is_logged_in is not available,
        defaults to True (no authentication required).
    """
    if not HAS_STREAMLIT:
        return True
    
    try:
        # Try to access st.user.is_logged_in
        if hasattr(st, 'user') and hasattr(st.user, 'is_logged_in'):
            return st.user.is_logged_in
        else:
            # If st.user.is_logged_in doesn't exist, assume logged in
            # This handles Streamlit Community Cloud and older versions
            return True
    except (AttributeError, KeyError):
        # If any error occurs, default to allowing access
        return True


def login():
    """
    Safely call st.login if available.
    """
    if HAS_STREAMLIT:
        try:
            if hasattr(st, 'login'):
                st.login()
        except (AttributeError, Exception):
            pass  # Login not available, skip


def logout():
    """
    Safely call st.logout if available.
    """
    if HAS_STREAMLIT:
        try:
            if hasattr(st, 'logout'):
                st.logout()
            else:
                # Fallback: clear session state
                if 'user_id' in st.session_state:
                    del st.session_state['user_id']
        except (AttributeError, Exception):
            # Fallback: clear session state
            if 'user_id' in st.session_state:
                del st.session_state['user_id']

