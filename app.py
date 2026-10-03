"""BuildPay AI - entry point. Run with: streamlit run app.py"""
import streamlit as st

st.set_page_config(page_title="BuildPay AI", page_icon="🏗️", layout="wide")

import pages  # noqa: E402
import ui  # noqa: E402
from db import init_db, q  # noqa: E402

init_db()
ui.inject_css()
pid = pages.sidebar()
role = st.session_state.get("role", "Contractor")

if role == "Content Studio":
    ui.hero("BuildPay AI", "Content Studio — post, caption & hashtags for your platform")
else:
    project = q("SELECT name, size FROM projects WHERE id=?", (pid,))[0] if pid else None
    ui.hero("BuildPay AI", f"{role} workspace" + (f" · {project['name']} ({project['size']})" if project else ""))

flash = st.session_state.pop("flash", None)
if flash:
    st.toast(flash, icon="✅")

if role == "Content Studio":
    pages.studio()
elif pid is None:
    st.info("👈 Create your first project in the sidebar to begin.")
else:
    {"Contractor": pages.contractor, "Consultant": pages.consultant,
     "Client": pages.client, "Records & Audit": pages.records}[role](pid)
