"""Shared agent foundation: Groq call + BaseAgent.
Every agent first calls its TOOLS (deterministic facts), then asks the LLM to interpret them."""
import json
import os
import time

import streamlit as st
from groq import Groq

RULES = (
    "Rules: AI prepares, checks, calculates and flags; humans authorize. Never approve, reject or "
    "certify anything and never imply a human approval. Use ONLY the facts supplied. Do no "
    "arithmetic - quote the numbers given. If evidence is unavailable or insufficient, say so "
    "explicitly. Answer with short bullet points in under 130 words."
)


def has_secret_key():
    """True when the key comes from Streamlit Secrets or an environment variable."""
    try:
        if st.secrets["GROQ_API_KEY"]:
            return True
    except Exception:
        pass
    return bool(os.environ.get("GROQ_API_KEY"))


def get_key():
    try:
        return st.secrets["GROQ_API_KEY"]
    except Exception:
        return os.environ.get("GROQ_API_KEY") or st.session_state.get("key_input")


def ask_llm(system, user, max_tokens=1500, temperature=0.2):
    key = get_key()
    if not key:
        return "⚠️ Agent error: GROQ_API_KEY is not configured."
    model = st.session_state.get("model", "openai/gpt-oss-120b")
    extra = {"extra_body": {"reasoning_effort": "low"}} if "gpt-oss" in model else {}
    for attempt in range(3):
        try:
            resp = Groq(api_key=key).chat.completions.create(
                model=model, temperature=temperature, max_tokens=max_tokens,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                **extra)
            text = (resp.choices[0].message.content or "").strip()
            return text or "⚠️ Agent error: empty response - try again or switch model."
        except Exception as e:  # errors stay visible - never silently approve
            if attempt < 2 and ("429" in str(e) or "rate" in str(e).lower()):
                time.sleep(8 * (attempt + 1))
                continue
            return f"⚠️ Agent error: {e}"


class BaseAgent:
    key = "agent"
    name = "Agent"
    icon = "🤖"
    role = ""
    task = ""        # what the LLM is asked to do
    doing = ""       # short text shown in the UI while the agent is working
    max_tokens = 1500
    temperature = 0.2

    def __init__(self):
        self.tools_used = []

    def use(self, tool, *args, **kwargs):
        """Call a tool and remember its name (shown in the UI)."""
        self.tools_used.append(tool.__name__)
        return tool(*args, **kwargs)

    def gather(self, ctx):
        """Call tools and return facts. Overridden by each agent."""
        raise NotImplementedError

    def task_for(self, ctx):
        return self.task

    def system_prompt(self):
        return (f"You are the {self.name} in BuildPay AI, a construction payment and work-approval "
                f"platform. Role: {self.role}\n{RULES}")

    def user_prompt(self, facts, ctx):
        return f"Task: {self.task_for(ctx)}\n\nFacts (deterministic tool outputs):\n{json.dumps(facts, indent=1, default=str)}"

    def run(self, ctx):
        self.tools_used = []
        facts = self.gather(ctx)
        if facts.get("_skip"):
            analysis = facts["_skip"]
        else:
            analysis = ask_llm(self.system_prompt(), self.user_prompt(facts, ctx),
                               self.max_tokens, self.temperature)
        return {"agent": self.name, "icon": self.icon, "tools": list(dict.fromkeys(self.tools_used)),
                "facts": facts, "analysis": analysis}
