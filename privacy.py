import streamlit as st

def password_gate():
    """Optional password gate via Streamlit Secrets.

    Set APP_PASSWORD in .streamlit/secrets.toml (local) or Streamlit Cloud Secrets.
    If not set, the app remains open.
    """
    pwd = st.secrets.get("APP_PASSWORD")
    if not pwd:
        return True

    st.sidebar.markdown("### Acesso")
    entered = st.sidebar.text_input("Senha", type="password")
    if entered == pwd:
        return True

    st.sidebar.error("Acesso restrito. Informe a senha.")
    st.stop()

def safe_warning(msg: str):
    st.warning(msg)

def mask_name(name: str) -> str:
    """Mask name to reduce PII exposure in presentation mode."""
    if not isinstance(name, str) or not name.strip():
        return ""
    parts = [p for p in name.strip().split() if p]
    if not parts:
        return ""
    first = parts[0]
    last = parts[-1] if len(parts) > 1 else ""
    return f"{first} {last[:1]}."
