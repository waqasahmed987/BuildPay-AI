"""Look & feel: CSS, hero banner, KPI cards, status pills, stepper and live agent tracker."""
import streamlit as st

from config import STATUS_TONE

CSS = """
<style>
.block-container{padding-top:1.4rem;max-width:1250px}
.hero{background:linear-gradient(120deg,#0f172a 0%,#1e3a8a 55%,#0ea5e9 100%);border-radius:22px;
  padding:28px 34px;margin-bottom:18px;box-shadow:0 12px 32px rgba(14,165,233,.25)}
.hero, .hero *{color:#fff !important}
.hero h1{margin:0;font-size:2.1rem;font-weight:800;letter-spacing:-.02em}
.hero p{margin:6px 0 0;opacity:.88;font-size:1rem}
.hero .tag{display:inline-block;margin-top:12px;padding:4px 12px;border-radius:999px;
  background:rgba(255,255,255,.16);font-size:.8rem;font-weight:600}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin:6px 0 16px}
.kpi{border:1px solid rgba(128,128,128,.25);border-radius:16px;padding:14px 18px;
  background:rgba(128,128,128,.07);transition:transform .15s}
.kpi:hover{transform:translateY(-2px)}
.kpi .l{font-size:.72rem;text-transform:uppercase;letter-spacing:.07em;opacity:.7;font-weight:600}
.kpi .v{font-size:1.9rem;font-weight:800;line-height:1.2}
.kpi.green .v{color:#10b981}.kpi.blue .v{color:#0ea5e9}.kpi.amber .v{color:#f59e0b}.kpi.red .v{color:#ef4444}
.pill{display:inline-block;padding:2px 11px;border-radius:999px;font-size:.74rem;font-weight:700}
.pill.green{background:rgba(16,185,129,.16);color:#10b981}.pill.blue{background:rgba(14,165,233,.16);color:#0ea5e9}
.pill.amber{background:rgba(245,158,11,.16);color:#f59e0b}.pill.orange{background:rgba(249,115,22,.16);color:#f97316}
.pill.red{background:rgba(239,68,68,.16);color:#ef4444}
.steps{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-bottom:14px}
.step{border:1px solid rgba(128,128,128,.25);border-radius:14px;padding:10px 14px;font-size:.85rem;font-weight:600;
  background:rgba(128,128,128,.05)}
.step small{display:block;opacity:.65;font-weight:500}
.step.done{border-color:#10b981;background:rgba(16,185,129,.10)}
.step.active{border-color:#0ea5e9;background:rgba(14,165,233,.12)}
.tracker{border:1px solid rgba(14,165,233,.45);border-radius:18px;padding:16px 18px;margin:8px 0 14px;
  background:rgba(14,165,233,.06)}
.now{font-size:1.05rem;margin-bottom:12px;display:flex;align-items:center;gap:10px}
.now.done{color:#10b981;font-weight:700}
.dot{width:12px;height:12px;border-radius:50%;background:#0ea5e9;display:inline-block;animation:pulse 1.2s infinite}
.chips{display:flex;flex-wrap:wrap;gap:8px}
.chip{border:1px solid rgba(128,128,128,.3);border-radius:999px;padding:5px 13px;font-size:.8rem;font-weight:600;opacity:.6}
.chip.work{opacity:1;border-color:#0ea5e9;background:rgba(14,165,233,.18);animation:pulse 1.2s infinite}
.chip.done{opacity:1;border-color:#10b981;background:rgba(16,185,129,.12)}
.chip.error{opacity:1;border-color:#ef4444;background:rgba(239,68,68,.12)}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(14,165,233,.55)}70%{box-shadow:0 0 0 10px rgba(14,165,233,0)}
  100%{box-shadow:0 0 0 0 rgba(14,165,233,0)}}
.aitag{font-size:.75rem;font-weight:700;letter-spacing:.05em;color:#0ea5e9}
.humantag{font-size:.75rem;font-weight:700;letter-spacing:.05em;color:#f59e0b}
div[data-testid="stSidebar"] .stRadio label{padding:2px 0}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def hero(title, subtitle):
    st.markdown(f'<div class="hero"><h1>🏗️ {title}</h1><p>{subtitle}</p>'
                '<span class="tag">AI prepares · checks · calculates · flags &nbsp;|&nbsp; Humans authorize</span></div>',
                unsafe_allow_html=True)


def kpis(items):
    """items = [(label, value, tone)]"""
    cards = "".join(f'<div class="kpi {t}"><div class="l">{l}</div><div class="v">{v}</div></div>' for l, v, t in items)
    st.markdown(f'<div class="kpis">{cards}</div>', unsafe_allow_html=True)


def pill(text, tone="blue"):
    return f'<span class="pill {tone}">{text}</span>'


def status_pill(status):
    return pill(status, STATUS_TONE.get(status, "blue"))


def stepper(steps):
    """steps = [(label, hint, state)] with state done / active / todo"""
    html = "".join(f'<div class="step {s}">{"✅ " if s == "done" else ""}{l}<small>{h}</small></div>' for l, h, s in steps)
    st.markdown(f'<div class="steps">{html}</div>', unsafe_allow_html=True)


def render_tracker(holder, agents, states, current):
    """Live agent tracker. Shows WHICH agent is working right now."""
    icons = {"wait": "⏳", "work": "⚡", "done": "✅", "error": "⚠️"}
    chips = "".join(f'<div class="chip {s}">{icons[s]} {a.icon} {a.name}</div>' for a, s in zip(agents, states))
    if current is not None:
        a = agents[current]
        now = f'<div class="now"><span class="dot"></span><b>{a.icon} {a.name}</b> — Working · <i>{a.doing}…</i></div>'
    else:
        now = '<div class="now done">✅ All agents finished — awaiting human decision</div>'
    holder.markdown(f'<div class="tracker">{now}<div class="chips">{chips}</div></div>', unsafe_allow_html=True)
