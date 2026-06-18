import json
import logging
from backend.app.agents.base import BaseAgent

logger = logging.getLogger(__name__)

REFLECTION_PROMPT = """You are the JARVIS Reflection Agent.
Your job is to analyze the user's daily telemetry data (completed tasks, pending tasks, application focus logs, attention efficiency rating, active goals, opportunities, and risks) and generate a daily retrospective reflection report.

Identify successes (tasks finished), bottlenecks (overdue tasks, high attention drift/distractions), and propose adjustments (workflow improvements or priority shifts).

Provide output strictly in the following JSON format:
{
  "summary": "Overview of today's activities",
  "what_worked": "Positive outcomes and completed tasks",
  "what_failed": "Bottlenecks, unresolved risks, or attention drift",
  "adjustments": "Recommended adjustments to workflows, priorities, or memory focus."
}
"""

class ReflectionAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="reflection",
            system_prompt=REFLECTION_PROMPT
        )

    def generate_reflection_report(self, telemetry_data: dict) -> dict:
        """
        Runs LLM inference on daily telemetry metrics.
        """
        if not self.model:
            # Formulate fallback based on telemetry
            completed_count = len(telemetry_data.get("completed_tasks", []))
            active_proj = telemetry_data.get("active_project", "JARVIS")
            efficiency = telemetry_data.get("focus_efficiency", 100.0)
            
            return {
                "summary": f"Completed active monitoring of project: {active_proj}.",
                "what_worked": f"Successfully advanced tasks. Completed {completed_count} subtasks.",
                "what_failed": "Observed minor context-switching but no critical blockers." if efficiency >= 70.0 else "Focus efficiency was low, indicating potential distractions.",
                "adjustments": f"Maintain alignment on active goals, especially regarding reflection and self-improvement."
            }

        prompt = f"Please analyze this daily telemetry: {json.dumps(telemetry_data)}"
        raw_response = self.run(prompt)
        
        try:
            # Find boundaries of the JSON block
            start = raw_response.find("{")
            end = raw_response.rfind("}") + 1
            if start != -1 and end != -1:
                return json.loads(raw_response[start:end])
            else:
                raise ValueError("No JSON boundaries found in response.")
        except Exception as e:
            logger.warning(f"Failed to parse Reflection Agent LLM response: {e}. Using fallback heuristically.")
            
            # Formulate fallback based on telemetry
            completed_count = len(telemetry_data.get("completed_tasks", []))
            active_proj = telemetry_data.get("active_project", "JARVIS")
            efficiency = telemetry_data.get("focus_efficiency", 100.0)
            
            return {
                "summary": f"Completed active monitoring of project: {active_proj}.",
                "what_worked": f"Successfully advanced tasks. Completed {completed_count} subtasks.",
                "what_failed": "Observed minor context-switching but no critical blockers." if efficiency >= 70.0 else "Focus efficiency was low, indicating potential distractions.",
                "adjustments": "Maintain alignment on active goals, avoid multitasking, and clear distraction categories."
            }
