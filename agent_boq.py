import tools
from agent_base import BaseAgent


class BoqAgent(BaseAgent):
    key = "boq"
    name = "BOQ & Activity Agent"
    icon = "📐"
    role = "Structures BOQ items, activities, units and original quantities."
    task = "Confirm this CR is linked to the correct BOQ activity and unit; flag any mismatch."
    doing = "Looking up the BOQ activity"

    def gather(self, ctx):
        cr = self.use(tools.cr_lookup, ctx["cr_id"])
        item = self.use(tools.boq_lookup, cr["boq_id"])
        return {"boq_item": {k: item[k] for k in ("code", "section", "description", "unit", "qty", "rate")},
                "check_request": {"cr_no": cr["cr_no"], "requested_qty": cr["req_qty"],
                                  "description": cr["description"]}}
