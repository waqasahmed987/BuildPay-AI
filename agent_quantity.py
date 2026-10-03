import tools
from agent_base import BaseAgent


class QuantityAgent(BaseAgent):
    key = "quantity"
    name = "Measurement & Quantity Agent"
    icon = "📏"
    role = "Checks requested, executed and cumulative quantities."
    task = "Assess requested vs approved and cumulative quantities and any overrun risk."
    doing = "Checking quantities and overrun risk"

    def gather(self, ctx):
        cr = self.use(tools.cr_lookup, ctx["cr_id"])
        s = self.use(tools.quantity_calculator, cr["boq_id"])
        approved_crs = self.use(tools.approved_cr_quantity, cr["boq_id"], ctx["cr_id"])
        projected = round(approved_crs + cr["req_qty"], 3)
        return {"quantities": s, "approved_cr_quantity_so_far": round(approved_crs, 3),
                "projected_with_this_cr": projected,
                "exceeds_approved_qty": projected > s["approved_qty"]}
