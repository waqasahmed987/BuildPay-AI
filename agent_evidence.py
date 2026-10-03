import tools
from agent_base import BaseAgent


class EvidenceAgent(BaseAgent):
    key = "evidence"
    name = "Document & Evidence Agent"
    icon = "📎"
    role = "Checks required documents and identifies missing or inconsistent evidence."
    task = ("Review evidence completeness and consistency with the CR description. "
            "State clearly what is missing or unreadable. Uploaded is not the same as verified.")
    doing = "Checking required documents"

    def gather(self, ctx):
        cr = self.use(tools.cr_lookup, ctx["cr_id"])
        return {"cr_description": cr["description"],
                "document_check": self.use(tools.required_document_checker, ctx["cr_id"]),
                "document_excerpts": self.use(tools.document_excerpts, ctx["cr_id"])}
