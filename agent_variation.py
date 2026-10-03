import tools
from agent_base import BaseAgent


class VariationAgent(BaseAgent):
    key = "variation"
    name = "Variation in Quantity Agent"
    icon = "🔀"
    role = "Identifies overruns, calculates additional quantities, summarizes justification and submits variations."
    task = ("Write a concise justification summary for this quantity variation using the contractor's note. "
            "Say if evidence for the justification is not provided.")
    doing = "Calculating the quantity variation"

    def gather(self, ctx):
        s = self.use(tools.quantity_calculator, ctx["boq_id"])
        pending = self.use(tools.pending_variation_qty, ctx["boq_id"])
        additional = round(s["overrun"] - pending, 3)
        if additional <= 0:
            return {"variation": None, "_skip": "No unsubmitted overrun - no variation required."}
        data = {"original_boq_qty": s["original_qty"], "previous_approved_variation": s["approved_variation_qty"],
                "current_approved_qty": s["approved_qty"], "previously_certified_qty": s["certified_previous"],
                "required_cumulative_qty": s["measured_cumulative"], "proposed_additional_qty": additional,
                "revised_proposed_qty": round(s["approved_qty"] + additional, 3), "boq_rate": s["rate"],
                "estimated_variation_value": round(additional * s["rate"], 2)}
        return {"item": f"{s['code']} {s['description']}", "unit": s["unit"], "variation": data,
                "contractor_note": ctx.get("note") or "(none provided)"}
