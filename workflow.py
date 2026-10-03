"""Orchestration: runs agent pipelines and performs workflow actions."""
import json

import streamlit as st

import tools
import ui
from agent_audit import AuditAgent
from agent_boq import BoqAgent
from agent_compliance import ComplianceAgent
from agent_cr import CheckRequestAgent
from agent_evidence import EvidenceAgent
from agent_history import HistoryAgent
from agent_ipc import IpcAgent
from agent_quantity import QuantityAgent
from agent_variation import VariationAgent
from db import ex, now, q

CR_PIPELINE = [BoqAgent, CheckRequestAgent, EvidenceAgent, QuantityAgent, ComplianceAgent, HistoryAgent, AuditAgent]


def run_pipeline(agent_classes, ctx):
    """Run agents one by one while the UI shows the agent that is working now."""
    agents = [cls() for cls in agent_classes]
    ctx = {**ctx, "results": {}}
    states = ["wait"] * len(agents)
    holder = st.empty()
    for i, agent in enumerate(agents):
        states[i] = "work"
        ui.render_tracker(holder, agents, states, i)
        result = agent.run(ctx)
        ctx["results"][agent.key] = result
        states[i] = "error" if result["analysis"].startswith("⚠️") else "done"
    ui.render_tracker(holder, agents, states, None)
    return ctx["results"]


def create_project(name, size, contract):
    items = tools.load_boq_file(size)  # read the Excel BOQ first, so a missing file creates nothing
    pid = ex("INSERT INTO projects(name,size,contract) VALUES(?,?,?)", (name, size, contract))
    for it in items:
        ex("INSERT INTO boq(project_id,code,section,description,unit,qty,rate) VALUES(?,?,?,?,?,?,?)",
           (pid, it["code"], it["section"], it["description"], it["unit"], it["qty"], it["rate"]))
    tools.audit_recorder("Project created", "Project", pid, f"{name} / {size} / {len(items)} BOQ items loaded from Excel")
    return pid


def submit_cr(pid, boq_id, qty, description, files):
    n = q("SELECT COUNT(*) n FROM crs WHERE project_id=?", (pid,))[0]["n"] + 1
    cid = ex("INSERT INTO crs(project_id,cr_no,boq_id,req_qty,description,status,created) VALUES(?,?,?,?,?,?,?)",
             (pid, f"CR-{n:03d}", boq_id, qty, description, "Submitted", now()))
    tools.save_documents("CR", cid, files)
    tools.audit_recorder("Check Request submitted", "CR", cid, f"qty {qty}")
    return cid


def review_cr(cr_id):
    results = run_pipeline(CR_PIPELINE, {"cr_id": cr_id, "entity": "CR", "entity_id": cr_id})
    brief = results.pop("audit")["analysis"]
    findings = {k: {"agent": v["agent"], "icon": v["icon"], "tools": v["tools"], "analysis": v["analysis"]}
                for k, v in results.items()}
    ex("UPDATE crs SET findings=?, brief=?, status='AI Reviewed' WHERE id=?", (json.dumps(findings), brief, cr_id))


def record_measurement(pid, cr_id, boq_id, qty, mdate, verifier, evidence):
    mid = ex("INSERT INTO measurements(project_id,cr_id,boq_id,qty,mdate,verifier,evidence) VALUES(?,?,?,?,?,?,?)",
             (pid, cr_id, boq_id, qty, str(mdate), verifier, evidence))
    tools.audit_recorder("Measurement recorded", "Measurement", mid, f"qty {qty}")


def create_variation(boq_id, note):
    results = run_pipeline([VariationAgent], {"boq_id": boq_id, "note": note})
    r = results["variation"]
    data = r["facts"].get("variation")
    if not data:
        return False
    pid = tools.boq_lookup(boq_id)["project_id"]
    n = q("SELECT COUNT(*) n FROM variations WHERE project_id=?", (pid,))[0]["n"] + 1
    vid = ex("INSERT INTO variations(project_id,var_no,cr_id,boq_id,data,additional,value,status,justification) "
             "VALUES(?,?,?,?,?,?,?,?,?)",
             (pid, f"VAR-{n:03d}", tools.latest_measurement_cr(boq_id), boq_id, json.dumps(data),
              data["proposed_additional_qty"], data["estimated_variation_value"], "Submitted", r["analysis"]))
    tools.audit_recorder("Variation submitted for human approval", "Variation", vid,
                         f"+{data['proposed_additional_qty']}")
    return True


def generate_ipc(pid, period, retention, other):
    lines, _ = tools.build_ipc_lines(pid)
    if not lines:
        return False
    ctx = {"project_id": pid, "retention": retention, "other": other, "entity": "Project", "entity_id": pid}
    results = run_pipeline([IpcAgent, AuditAgent], ctx)
    facts = results["ipc"]["facts"]
    review = results["ipc"]["analysis"] + "\n\n" + results["audit"]["analysis"]
    n = q("SELECT COUNT(*) n FROM ipcs WHERE project_id=?", (pid,))[0]["n"] + 1
    iid = ex("INSERT INTO ipcs(project_id,ipc_no,period,lines_json,totals,exceptions,status,review,created) "
             "VALUES(?,?,?,?,?,?,?,?,?)",
             (pid, f"IPC-{n:02d}", period, json.dumps(facts["lines"]), json.dumps(facts["totals"]),
              json.dumps(facts["exceptions"]), "Draft", review, now()))
    tools.audit_recorder("IPC draft generated", "IPC", iid, f"net {facts['totals']['net']}")
    return True


def record_decision(entity, entity_id, table, choice, comment):
    """Human-only decision. `table` is an internal constant, never user input."""
    status = {"Approve": "Approved", "Return": "Returned", "Reject": "Rejected"}[choice]
    ex(f"UPDATE {table} SET status=? WHERE id=?", (status, entity_id))
    ex("INSERT INTO approvals(entity,entity_id,decision,role,person,comment,ts) VALUES(?,?,?,?,?,?,?)",
       (entity, entity_id, status, st.session_state.get("role"), st.session_state.get("person"), comment, now()))
    tools.audit_recorder(f"Human decision: {status}", entity, entity_id, comment)
