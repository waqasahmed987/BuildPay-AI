import tools
from agent_base import BaseAgent


class HistoryAgent(BaseAgent):
    key = "history"
    name = "History & Duplicate Detection Agent"
    icon = "🕘"
    role = "Compares current records with prior CRs, variations and IPCs."
    task = "Report possible duplicates and relevant prior CRs, variations and certified quantities."
    doing = "Searching past records for duplicates"

    def gather(self, ctx):
        cr = self.use(tools.cr_lookup, ctx["cr_id"])
        return self.use(tools.historical_record_query, cr["boq_id"], cr["id"], cr["req_qty"])
