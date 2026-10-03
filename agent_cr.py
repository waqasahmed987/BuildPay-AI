import tools
from agent_base import BaseAgent


class CheckRequestAgent(BaseAgent):
    key = "cr"
    name = "Check Request Agent"
    icon = "📝"
    role = "Prepares and validates Check Requests against approved BOQ activities."
    task = "Validate the CR: positive quantity, clear description, quantity within remaining approved quantity."
    doing = "Validating the Check Request"

    def gather(self, ctx):
        cr = self.use(tools.cr_lookup, ctx["cr_id"])
        s = self.use(tools.quantity_calculator, cr["boq_id"])
        return {"check_request": {"cr_no": cr["cr_no"], "boq_code": cr["code"], "unit": cr["unit"],
                                  "requested_qty": cr["req_qty"], "description": cr["description"]},
                "quantity_positive": cr["req_qty"] > 0,
                "description_provided": bool((cr["description"] or "").strip()),
                "remaining_approved_qty": s["remaining_approved"]}
