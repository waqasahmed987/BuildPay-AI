"""Constants and templates used across BuildPay AI."""

DB_PATH = "buildpay.db"
MODELS = ["openai/gpt-oss-120b", "llama-3.3-70b-versatile", "openai/gpt-oss-20b"]

ROLES = ["Contractor", "Consultant", "Client", "Records & Audit", "Content Studio"]
ROLE_ICONS = {"Contractor": "👷", "Consultant": "🧑‍🔧", "Client": "🏢",
              "Records & Audit": "🗂️", "Content Studio": "✍️"}

DOC_TYPES = ["pdf", "docx", "xlsx", "csv", "txt", "md"]

# BOQ templates are loaded from these Excel files (kept next to app.py in the GitHub repo)
BOQ_FILES = {
    "5 marla": "5_marla_double_storey_civil_boq.xlsx",
    "10 marla": "10_marla_double_storey_civil_boq.xlsx",
    "1 kanal": "1_kanal_double_storey_civil_boq.xlsx",
}
SECTIONS = ["Mobilization", "Grey Structure", "Finishing"]

# Required evidence per BOQ section: (label, keywords searched in file name / text)
REQUIRED_DOCS = {
    "Mobilization": [("Site layout / method statement", ["layout", "method", "mobil"]),
                     ("Site record / report", ["record", "report", "photo"])],
    "Grey Structure": [("Approved drawing / shop drawing", ["drawing", "shop", "dwg"]),
                       ("Material test report", ["test", "cube", "material"]),
                       ("Inspection checklist", ["checklist", "inspection"])],
    "Finishing": [("Material approval / sample", ["material", "sample", "approval"]),
                  ("Inspection checklist", ["checklist", "inspection"])],
}

STATUS_TONE = {"Submitted": "amber", "AI Reviewed": "blue", "Approved": "green",
               "Returned": "orange", "Rejected": "red", "Draft": "amber"}

PLATFORM_RULES = {
    "LinkedIn": "120-220 words, strong first-line hook, short paragraphs, end with a question or call to action.",
    "Facebook": "80-150 words, conversational, one clear call to action.",
    "Instagram": "60-120 words, punchy lines, a few emojis, line breaks for readability.",
    "X (Twitter)": "The post must be 280 characters or fewer. One idea, no filler.",
    "WhatsApp Channel": "50-100 words, direct and friendly, a few emojis.",
}
