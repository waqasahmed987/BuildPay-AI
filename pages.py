"""Streamlit screens: sidebar, role workspaces, records and content studio."""
import json
from datetime import date

import pandas as pd
import streamlit as st

import agent_base
import config
import tools
import ui
import workflow
from agent_content import ContentAgent
from db import q


# ---------------------------------------------------------------- shared pieces
def boq_table(pid):
    rows = []
    for it in q("SELECT id FROM boq WHERE project_id=? ORDER BY id", (pid,)):
        s = tools.quantity_calculator(it["id"])
        rows.append({"Code": s["code"], "Description": s["description"], "Unit": s["unit"], "Rate": s["rate"],
                     "Original Qty": s["original_qty"], "Amount (PKR)": round(s["original_qty"] * s["rate"], 2),
                     "Approved Qty": s["approved_qty"],
                     "Measured": s["measured_cumulative"], "Certified": s["certified_previous"],
                     "Overrun": s["overrun"]})
    return pd.DataFrame(rows)


def boq_summary(pid):
    """Section totals, like the Summary sheet of the Excel BOQ."""
    rows = {r["section"]: r["a"] for r in q("SELECT section, SUM(qty*rate) a FROM boq WHERE project_id=? GROUP BY section", (pid,))}
    cards = [("Total BOQ (PKR)", f"{sum(rows.values()):,.0f}", "blue")]
    cards += [(sec, f"{rows[sec]:,.0f}", "green") for sec in config.SECTIONS if sec in rows]
    ui.kpis(cards)


def decision_box(entity, entity_id, table, options, key):
    with st.container(border=True):
        st.markdown('<span class="humantag">👤 HUMAN DECISION — only a person can approve</span>', unsafe_allow_html=True)
        c1, c2 = st.columns([1, 3])
        choice = c1.selectbox("Decision", options, key=f"d_{key}")
        comment = c2.text_input("Comments", key=f"c_{key}")
        if st.button("Record decision", key=f"b_{key}", type="primary"):
            if not st.session_state.get("person"):
                st.error("Enter your name in the sidebar first.")
            else:
                workflow.record_decision(entity, entity_id, table, choice, comment)
                st.session_state["flash"] = f"{entity} decision recorded: {choice}"
                st.rerun()


def ai_block(title, text):
    st.markdown(f'<span class="aitag">🤖 {title} — advisory, not an approval</span>', unsafe_allow_html=True)
    st.info(text)


def cr_list(pid):
    role = st.session_state.role
    can_decide = role in ("Consultant", "Client")
    crs = q("SELECT c.*, b.code, b.description AS item, b.unit FROM crs c JOIN boq b ON b.id=c.boq_id "
            "WHERE c.project_id=? ORDER BY c.id DESC", (pid,))
    if not crs:
        st.info("No Check Requests yet.")
    for cr in crs:
        with st.expander(f"{cr['cr_no']} · {cr['code']} {cr['item']} · {cr['req_qty']} {cr['unit']} · {cr['status']}"):
            st.markdown(ui.status_pill(cr["status"]), unsafe_allow_html=True)
            st.write(cr["description"] or "_No description_")
            docs = q("SELECT filename FROM docs WHERE entity='CR' AND entity_id=?", (cr["id"],))
            st.caption("Evidence uploaded (not verified): " + (", ".join(d["filename"] for d in docs) or "none"))
            if cr["status"] in ("Submitted", "AI Reviewed", "Returned"):
                if role == "Contractor":
                    more = st.file_uploader("Add evidence", type=config.DOC_TYPES, accept_multiple_files=True,
                                            key=f"up{cr['id']}")
                    if more and st.button("Attach files", key=f"at{cr['id']}"):
                        tools.save_documents("CR", cr["id"], more)
                        tools.audit_recorder("Evidence added", "CR", cr["id"], f"{len(more)} file(s)")
                        st.rerun()
                if st.button("🤖 Run multi-agent AI review", key=f"rv{cr['id']}", type="primary"):
                    workflow.review_cr(cr["id"])
                    st.session_state["flash"] = f"AI review finished for {cr['cr_no']}"
                    st.rerun()
            if cr["brief"]:
                ai_block("Review & Audit Agent brief", cr["brief"])
                st.markdown("**Findings by agent**")
                for f in json.loads(cr["findings"]).values():
                    st.markdown(f"{f['icon']} **{f['agent']}**  \n"
                                f"<small>Tools used: {', '.join(f['tools'])}</small>", unsafe_allow_html=True)
                    st.write(f["analysis"])
            if can_decide and cr["status"] == "AI Reviewed":
                decision_box("CR", cr["id"], "crs", ["Approve", "Return", "Reject"], f"cr{cr['id']}")
            elif can_decide and cr["status"] == "Submitted":
                st.caption("Run the AI review before recording a decision.")


def variation_list(pid, can_decide):
    rows = q("SELECT * FROM variations WHERE project_id=? ORDER BY id DESC", (pid,))
    if not rows:
        st.info("No variations yet.")
    for v in rows:
        d = json.loads(v["data"])
        item = q("SELECT code, unit FROM boq WHERE id=?", (v["boq_id"],))[0]
        with st.expander(f"{v['var_no']} · {item['code']} · +{v['additional']} {item['unit']} · "
                         f"value {v['value']:,.2f} · {v['status']}"):
            st.markdown(ui.status_pill(v["status"]), unsafe_allow_html=True)
            st.dataframe(pd.DataFrame({"Field": [k.replace("_", " ").title() for k in d],
                                       "Value": [str(x) for x in d.values()]}), hide_index=True)
            ai_block("Variation in Quantity Agent summary", v["justification"])
            if can_decide and v["status"] == "Submitted":
                decision_box("Variation", v["id"], "variations", ["Approve", "Return", "Reject"], f"var{v['id']}")


def ipc_list(pid, can_decide):
    rows = q("SELECT * FROM ipcs WHERE project_id=? ORDER BY id DESC", (pid,))
    if not rows:
        st.info("No IPCs yet.")
    for ipc in rows:
        t = json.loads(ipc["totals"])
        with st.expander(f"{ipc['ipc_no']} · {ipc['period']} · net {t['net']:,.2f} · {ipc['status']}"):
            st.markdown(ui.status_pill(ipc["status"]), unsafe_allow_html=True)
            df = pd.DataFrame(json.loads(ipc["lines_json"])).drop(columns=["boq_id"])
            st.dataframe(df, hide_index=True)
            ui.kpis([("Gross", f"{t['gross']:,.0f}", "blue"), (f"Retention {t['retention_pct']}%", f"{t['retention']:,.0f}", "amber"),
                     ("Other deductions", f"{t['other_deductions']:,.0f}", "amber"), ("Net (draft)", f"{t['net']:,.0f}", "green")])
            for e in json.loads(ipc["exceptions"]):
                st.warning(e)
            ai_block("IPC & Review Agents", ipc["review"])
            st.download_button("⬇️ IPC lines (CSV)", df.to_csv(index=False), f"{ipc['ipc_no']}.csv", key=f"dl{ipc['id']}")
            if can_decide and ipc["status"] == "Draft":
                decision_box("IPC", ipc["id"], "ipcs", ["Approve", "Return"], f"ipc{ipc['id']}")


def overview(pid):
    crs = q("SELECT status FROM crs WHERE project_id=?", (pid,))
    vars_ = q("SELECT status FROM variations WHERE project_id=?", (pid,))
    ipcs = q("SELECT status FROM ipcs WHERE project_id=?", (pid,))
    meas = q("SELECT 1 FROM measurements WHERE project_id=?", (pid,))
    overruns = int((boq_table(pid)["Overrun"] > 0).sum())
    ui.kpis([
        ("Open CRs", sum(c["status"] in ("Submitted", "AI Reviewed") for c in crs), "amber"),
        ("Approved CRs", sum(c["status"] == "Approved" for c in crs), "green"),
        ("Pending variations", sum(v["status"] == "Submitted" for v in vars_), "blue"),
        ("Overrun items", overruns, "red" if overruns else "green"),
        ("IPCs approved", sum(i["status"] == "Approved" for i in ipcs), "green"),
    ])
    done = [bool(crs), any(c["status"] != "Submitted" for c in crs), any(c["status"] == "Approved" for c in crs),
            bool(meas), any(i["status"] == "Approved" for i in ipcs)]
    labels = [("Check Request", "Contractor submits"), ("Inspection", "AI + engineer review"),
              ("Approval", "Human decision"), ("Quantity Verification", "Measure & check"), ("IPC", "Certify payment")]
    first_open = done.index(False) if False in done else -1
    ui.stepper([(l, h, "done" if d else ("active" if i == first_open else "todo"))
                for i, ((l, h), d) in enumerate(zip(labels, done))])


# ---------------------------------------------------------------- workspaces
def contractor(pid):
    overview(pid)
    t0, t1, t2, t3, t4 = st.tabs(["📊 BOQ", "📝 Check Requests", "📏 Execution & Measurement", "🔀 Variations", "🧾 IPC"])

    with t0:
        boq_summary(pid)
        df = boq_table(pid)
        st.dataframe(df, hide_index=True)
        st.download_button("⬇️ BOQ progress (CSV)", df.to_csv(index=False), "boq_progress.csv")

    with t1:
        items = {i["id"]: i for i in q("SELECT * FROM boq WHERE project_id=? ORDER BY id", (pid,))}
        with st.container(border=True):
            st.markdown("##### New Check Request")
            with st.form("new_cr", clear_on_submit=True):
                bid = st.selectbox("BOQ activity", list(items),
                                   format_func=lambda i: f"{items[i]['code']} — {items[i]['description']} ({items[i]['unit']})")
                qty = st.number_input("Requested quantity", min_value=0.0, step=1.0, format="%.2f")
                desc = st.text_area("Description / execution context")
                files = st.file_uploader("Supporting evidence", type=config.DOC_TYPES, accept_multiple_files=True)
                if st.form_submit_button("Submit Check Request", type="primary"):
                    if qty <= 0:
                        st.error("Requested quantity must be greater than zero.")
                    else:
                        workflow.submit_cr(pid, bid, qty, desc, files)
                        st.session_state["flash"] = "Check Request submitted"
                        st.rerun()
        cr_list(pid)

    with t2:
        approved = q("SELECT c.id, c.cr_no, c.boq_id, b.code, b.unit FROM crs c JOIN boq b ON b.id=c.boq_id "
                     "WHERE c.project_id=? AND c.status='Approved'", (pid,))
        if not approved:
            st.info("Measurements can only be recorded against human-approved Check Requests.")
        else:
            amap = {a["id"]: a for a in approved}
            with st.container(border=True):
                st.markdown("##### Record executed quantity")
                with st.form("measure", clear_on_submit=True):
                    cid = st.selectbox("Approved CR", list(amap),
                                       format_func=lambda i: f"{amap[i]['cr_no']} · {amap[i]['code']} ({amap[i]['unit']})")
                    qty = st.number_input("Executed quantity (current)", min_value=0.0, step=1.0, format="%.2f")
                    mdate = st.date_input("Measurement date", date.today())
                    verifier = st.text_input("Verifier")
                    evidence = st.text_area("Measurement evidence / comments")
                    if st.form_submit_button("Record measurement", type="primary"):
                        if qty > 0:
                            workflow.record_measurement(pid, cid, amap[cid]["boq_id"], qty, mdate, verifier, evidence)
                            st.session_state["flash"] = "Measurement recorded"
                            st.rerun()
                        else:
                            st.error("Executed quantity must be greater than zero.")
        ms = q("SELECT c.cr_no, b.code, m.qty, b.unit, m.mdate, m.verifier, m.evidence FROM measurements m "
               "JOIN crs c ON c.id=m.cr_id JOIN boq b ON b.id=m.boq_id WHERE m.project_id=? ORDER BY m.id DESC", (pid,))
        if ms:
            st.dataframe(pd.DataFrame(ms), hide_index=True)
        for _, r in boq_table(pid).iterrows():
            if r["Overrun"] > 0:
                st.warning(f"⚠️ {r['Code']}: measured {r['Measured']} exceeds approved {r['Approved Qty']} {r['Unit']} "
                           f"(overrun {r['Overrun']}). A variation is required before this quantity can enter an IPC.")

    with t3:
        st.caption("The Variation in Quantity Agent calculates and submits. Only the Client can approve.")
        for it in q("SELECT id FROM boq WHERE project_id=?", (pid,)):
            s = tools.quantity_calculator(it["id"])
            gap = round(s["overrun"] - tools.pending_variation_qty(it["id"]), 3)
            if gap > 0:
                with st.container(border=True):
                    st.warning(f"{s['code']} {s['description']}: overrun of {gap} {s['unit']} has no submitted variation.")
                    note = st.text_input("Justification note", key=f"vn{it['id']}")
                    if st.button("🤖 Run Variation Agent", key=f"vb{it['id']}", type="primary"):
                        if workflow.create_variation(it["id"], note):
                            st.session_state["flash"] = "Variation submitted for human approval"
                        st.rerun()
        variation_list(pid, False)

    with t4:
        has_draft = bool(q("SELECT 1 FROM ipcs WHERE project_id=? AND status='Draft'", (pid,)))
        c1, c2 = st.columns(2)
        period = c1.text_input("Period", date.today().strftime("%B %Y"))
        other = c2.number_input("Other deductions", min_value=0.0, step=1000.0)
        if has_draft:
            st.info("A draft IPC is awaiting the Client's decision.")
        if st.button("🤖 Generate IPC draft", disabled=has_draft, type="primary"):
            if workflow.generate_ipc(pid, period, st.session_state.get("retention", 5.0), other):
                st.session_state["flash"] = "IPC draft generated"
                st.rerun()
            else:
                st.warning("No eligible approved work to certify yet.")
        ipc_list(pid, False)


def consultant(pid):
    overview(pid)
    st.markdown("#### Technical review of Check Requests")
    st.caption("Run the AI review, read the brief, then record your own decision.")
    cr_list(pid)


def client(pid):
    overview(pid)
    t1, t2, t3 = st.tabs(["📝 Check Requests", "🔀 Variations", "🧾 IPCs"])
    with t1:
        cr_list(pid)
    with t2:
        variation_list(pid, True)
    with t3:
        ipc_list(pid, True)


def records(pid):
    overview(pid)
    views = {
        "BOQ vs revised quantities": boq_table(pid),
        "Check Requests": pd.DataFrame(q("SELECT cr_no, boq_id, req_qty, status, created FROM crs WHERE project_id=?", (pid,))),
        "Variation Register": pd.DataFrame(q("SELECT var_no, boq_id, additional, value, status FROM variations WHERE project_id=?", (pid,))),
        "IPCs": pd.DataFrame(q("SELECT ipc_no, period, status, created FROM ipcs WHERE project_id=?", (pid,))),
        "Human decisions": pd.DataFrame(q("SELECT * FROM approvals ORDER BY id DESC")),
        "Audit trail": pd.DataFrame(q("SELECT * FROM audit ORDER BY id DESC")),
    }
    tabs = st.tabs(list(views))
    for tab, (name, df) in zip(tabs, views.items()):
        with tab:
            if df.empty:
                st.info("Nothing recorded yet.")
            else:
                st.dataframe(df, hide_index=True)
                st.download_button("⬇️ CSV", df.to_csv(index=False), f"{name.replace(' ', '_').lower()}.csv", key=f"r_{name}")


def studio():
    st.markdown("#### ✍️ Content Studio")
    st.caption("Generate a post, caption and hashtags to promote your platform.")
    with st.container(border=True):
        c1, c2 = st.columns(2)
        ctype = c1.selectbox("Content type", ["Product announcement", "Educational post", "Case study / success story",
                                              "Feature spotlight", "Problem-solution post", "Thought-leadership"])
        platform = c2.selectbox("Platform", list(config.PLATFORM_RULES))
        topic = st.text_area("Topic", "How AI digitizes check requests, inspections, approvals and IPCs "
                                      "for contractors, consultants and clients")
        audience = c1.selectbox("Target audience", ["Contractors", "Consultants / Engineers", "Clients / Developers",
                                                    "Project Managers", "Quantity Surveyors", "General construction industry"])
        tone = c2.selectbox("Tone", ["Professional", "Friendly", "Persuasive", "Technical", "Inspirational"])
        go = st.button("✨ Generate content", type="primary")
    if go:
        ctx = {"content_type": ctype, "platform": platform, "topic": topic, "audience": audience, "tone": tone}
        st.session_state["content"] = workflow.run_pipeline([ContentAgent], ctx)["content"]["analysis"]
    if st.session_state.get("content"):
        with st.container(border=True):
            st.markdown(st.session_state["content"])
        st.download_button("⬇️ Download (TXT)", st.session_state["content"], "post.txt")


# ---------------------------------------------------------------- sidebar
def sidebar():
    sb = st.sidebar
    sb.markdown("### 🏗️ BuildPay AI")
    sb.caption("Construction inspection, approval & IPC platform")
    sb.radio("Workspace", config.ROLES, key="role", format_func=lambda r: f"{config.ROLE_ICONS[r]}  {r}")
    sb.text_input("Your name", key="person", placeholder="Recorded in the audit trail")
    with sb.expander("⚙️ AI settings"):
        st.selectbox("Groq model", config.MODELS, key="model")
        if not agent_base.has_secret_key():
            st.text_input("Groq API key", type="password", key="key_input",
                          help="Use Streamlit Secrets when deployed.")
        st.number_input("Retention %", 0.0, 20.0, 5.0, 0.5, key="retention")
    sb.divider()

    projects = q("SELECT * FROM projects ORDER BY id")
    with sb.expander("➕ New project", expanded=not projects):
        name = st.text_input("Project name", key="np_name")
        size = st.selectbox("BOQ template (double-storey, civil)", list(config.BOQ_FILES), key="np_size")
        contract = st.text_area("Contract / specification requirements (optional)", key="np_contract")
        if st.button("Create project", key="np_btn") and name.strip():
            try:
                workflow.create_project(name.strip(), size, contract)
                st.session_state["flash"] = "Project created - BOQ loaded from Excel"
                st.rerun()
            except Exception as e:
                st.error(f"Could not load the BOQ: {e}")
    if not projects:
        return None
    pmap = {p["id"]: p for p in projects}
    pid = sb.selectbox("Project", list(pmap), format_func=lambda i: f"{pmap[i]['name']} ({pmap[i]['size']})")
    sb.caption("BOQ quantities and rates come from your Excel templates (illustrative). Validate against drawings, specifications and the contract.")
    return pid
