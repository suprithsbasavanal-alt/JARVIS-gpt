import json
import logging
from sqlalchemy.orm import Session
from backend.agents.base import BaseAgent
from backend.database import Task

logger = logging.getLogger(__name__)

PLANNER_PROMPT = """You are the JARVIS Planner Agent, the central reasoning engine of the JARVIS AI Operating Assistant.
Your job is to analyze user requests, understand their goals, and break them down into structured steps (tasks).

When a user gives a request:
1. Break it down into concrete sequential or parallel steps.
2. Each step should represent a single logical task that can be executed by a specialized agent (e.g. researcher, coder, writer, vision, automation, memory).
3. Respond in structured JSON format with a list of tasks.

JSON Format:
{
  "goal": "Overview of user goal",
  "steps": [
    {
      "title": "Task Title",
      "description": "Task Description",
      "agent": "researcher" | "coder" | "writer" | "vision" | "automation" | "memory",
      "dependencies": []
    }
  ]
}
"""

class PlannerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="planner",
            system_prompt=PLANNER_PROMPT
        )

    def create_plan(self, user_prompt: str, db: Session) -> dict:
        """
        Creates a plan for a user prompt, saves it to the database, and returns the steps.
        """
        raw_response = self.run(user_prompt)
        
        try:
            # Attempt to parse JSON plan from model response
            # Find the JSON block boundaries
            start = raw_response.find("{")
            end = raw_response.rfind("}") + 1
            if start != -1 and end != -1:
                plan_json = json.loads(raw_response[start:end])
            else:
                raise ValueError("No JSON block found")
        except Exception as e:
            logger.warning(f"Failed to parse LLM plan: {e}. Falling back to default plan.")
            plan_json = {
                "goal": user_prompt,
                "steps": [
                    {
                        "title": "Analyze and research",
                        "description": f"Perform initial research regarding: {user_prompt}",
                        "agent": "researcher",
                        "dependencies": []
                    },
                    {
                        "title": "Execute action plan",
                        "description": f"Formulate and execute output for: {user_prompt}",
                        "agent": "writer",
                        "dependencies": ["Analyze and research"]
                    }
                ]
            }

        # Save the tasks in the database
        created_tasks = []
        for step in plan_json["steps"]:
            task = Task(
                title=step["title"],
                description=step.get("description", ""),
                status="pending",
                assigned_agent=step["agent"]
            )
            db.add(task)
            db.commit()
            db.refresh(task)
            created_tasks.append(task)
            
        return {
            "goal": plan_json.get("goal", user_prompt),
            "tasks": [{"id": str(t.id), "title": t.title, "description": t.description, "status": t.status, "agent": t.assigned_agent} for t in created_tasks]
        }
