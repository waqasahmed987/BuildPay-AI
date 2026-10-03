import tools
from agent_base import BaseAgent


class ContentAgent(BaseAgent):
    key = "content"
    name = "Content Studio Agent"
    icon = "✍️"
    role = "Writes platform-ready posts, captions and hashtags for the construction industry."
    doing = "Writing your post, caption and hashtags"
    max_tokens = 2000
    temperature = 0.7

    def gather(self, ctx):
        return {"brief": {k: ctx[k] for k in ("content_type", "platform", "topic", "audience", "tone")},
                "platform_rules": self.use(tools.platform_rules, ctx["platform"])}

    def system_prompt(self):
        return ("You are an expert social-media copywriter for the construction and AEC industry. "
                "Never invent statistics, customers or testimonials.")

    def user_prompt(self, facts, ctx):
        b = facts["brief"]
        return (f"Create a {b['content_type']} for {b['platform']}.\nTopic: {b['topic']}\n"
                f"Target audience: {b['audience']}\nTone: {b['tone']}\n"
                f"Platform rules: {facts['platform_rules']}\n\n"
                "Return exactly three sections with these markdown headings:\n"
                "### Post\n(the full post text)\n### Caption\n(a short caption)\n"
                "### Hashtags\n(8-12 relevant hashtags)")
