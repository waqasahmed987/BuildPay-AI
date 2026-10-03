import tools
from agent_base import BaseAgent


class IpcAgent(BaseAgent):
    key = "ipc"
    name = "IPC Preparation & Reconciliation Agent"
    icon = "🧾"
    role = "Prepares IPC drafts from approved eligible work and reconciles values."
    task = "Reconcile this IPC draft: summarise what is certified this period, the totals, and any exceptions."
    doing = "Preparing and reconciling the IPC"

    def gather(self, ctx):
        lines, exceptions = self.use(tools.build_ipc_lines, ctx["project_id"])
        totals = self.use(tools.payment_calculator, lines, ctx["retention"], ctx["other"])
        return {"lines": lines, "exceptions": exceptions, "totals": totals}

    def user_prompt(self, facts, ctx):
        slim = [{k: l[k] for k in ("code", "unit", "previous_qty", "current_qty", "cumulative_qty", "amount")}
                for l in facts["lines"]]
        compact = {"lines": slim, "totals": facts["totals"], "exceptions": facts["exceptions"]}
        return super().user_prompt(compact, ctx)
