import streamlit as st

def initialize_session_state():
    """Initialize session state variables."""
    if 'extracted_text' not in st.session_state:
        st.session_state.extracted_text = None
    if 'summary' not in st.session_state:
        st.session_state.summary = None
    if 'risks' not in st.session_state:
        st.session_state.risks = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    # Add documents storage for document comparison
    if 'uploaded_docs' not in st.session_state:
        st.session_state.uploaded_docs = {}
    if 'main_doc_id' not in st.session_state:
        st.session_state.main_doc_id = None 
    if 'summaries' not in st.session_state:
        st.session_state.summaries = {}
    # GDPR consent state variables
    if 'gdpr_consent' not in st.session_state:
        st.session_state.gdpr_consent = False
    if 'show_gdpr_banner' not in st.session_state:
        st.session_state.show_gdpr_banner = True
    if 'show_privacy_policy' not in st.session_state:
        st.session_state.show_privacy_policy = False
