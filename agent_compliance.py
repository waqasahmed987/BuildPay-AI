import tools
from agent_base import BaseAgent


class ComplianceAgent(BaseAgent):
    key = "compliance"
    name = "Contract Compliance Agent"
    icon = "⚖️"
    role = "Checks the supplied contract/specification requirements."
    task = ("Check the CR against the supplied contract/specification text. "
            "If none is supplied, say that compliance cannot be assessed.")
    doing = "Checking contract requirements"

    def gather(self, ctx):
        cr = self.use(tools.cr_lookup, ctx["cr_id"])
        contract = self.use(tools.get_contract, cr["project_id"])
        return {"contract_requirements": contract[:3000] or "NONE SUPPLIED",
                "cr_description": cr["description"],
                "document_excerpts": self.use(tools.document_excerpts, ctx["cr_id"])}
