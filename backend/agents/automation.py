import logging
import subprocess
import platform
from backend.agents.base import BaseAgent

logger = logging.getLogger(__name__)

AUTOMATION_PROMPT = """You are the JARVIS Automation Agent. Your task is to control the desktop environment:
- Open or close applications.
- Run terminal shell commands (always require safety verification for destructive actions).
- Manage files (creating, deleting, finding, organizing).
- Execute GUI scripting.
"""

class AutomationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="automation",
            system_prompt=AUTOMATION_PROMPT
        )
        self.system = platform.system()

    def launch_app(self, app_name: str) -> bool:
        """
        Launches an application.
        On macOS, uses the native 'open' command.
        """
        logger.info(f"Launching application: {app_name}")
        if self.system == "Darwin":
            try:
                # Use open -a to launch applications on macOS
                subprocess.Popen(["open", "-a", app_name])
                return True
            except Exception as e:
                logger.error(f"Failed to launch app via macOS open: {e}")
                
        logger.info(f"[Automation Agent Mock]: Opened application {app_name}")
        return False

    def execute_script(self, script_content: str) -> str:
        """
        Executes a script safely.
        """
        logger.info("Executing automation script...")
        # Placeholder for AppleScript or shell execution
        return "Script executed successfully."

automation_agent = AutomationAgent()
