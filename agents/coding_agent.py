"""
agents/coding_agent.py
A specialized sub-agent for writing, debugging, and explaining code.
"""
import brain.llm as llm

class CodingAgent:
    def __init__(self):
        self.system_prompt = (
            "You are JARVIS-CODE, an expert, senior-level software engineering AI. "
            "Your sole purpose is to write optimized, clean, and highly efficient code. "
            "When responding to coding questions, always provide the code in Markdown blocks. "
            "Do not provide unnecessary filler text. Be direct, brilliant, and cinematic."
        )

    def execute(self, user_prompt):
        """Processes a coding-related query."""
        print("[AGENT] Routing to Coding Agent...")
        # We append a specific directive to ensure code generation
        enhanced_prompt = f"Write the optimal code for the following request: {user_prompt}"
        return llm.generate_response(enhanced_prompt, custom_system_prompt=self.system_prompt)
