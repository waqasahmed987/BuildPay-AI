import tools
from agent_base import BaseAgent


class AuditAgent(BaseAgent):
    key = "audit"
    name = "Review & Audit Agent"
    icon = "🛡️"
    role = "Consolidates findings and prepares human review/audit packages."
    doing = "Consolidating findings into a review brief"

    def task_for(self, ctx):
        what = "Check Request" if ctx["entity"] == "CR" else "IPC"
        return (f"Prepare the human review brief for this {what}: (1) key risks / blocking issues, "
                "(2) missing evidence, (3) an advisory AI recommendation (approve / return / reject). "
                "State clearly that a human decides.")

    def gather(self, ctx):
        findings = {r["agent"]: r["analysis"] for r in ctx["results"].values()}
        self.use(tools.audit_recorder, "AI review package prepared", ctx["entity"], ctx["entity_id"],
                 f"{len(findings)} agent(s) reported")
        return {"agent_findings": findings, **ctx.get("extra", {})}
