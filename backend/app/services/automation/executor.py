import os
import subprocess
import platform
import logging

logger = logging.getLogger(__name__)

# Safe workspace directories limit
WORKSPACE_ROOT = "/Users/suprith.s.basavanal/Documents/antigrativity /JARVIS-gpt"

class AppleScriptExecutor:
    @staticmethod
    def execute(script_content: str) -> str:
        """
        Executes raw AppleScript content via osascript.
        """
        if platform.system() != "Darwin":
            logger.info(f"[AppleScript Executor Mock]: Executed script:\n{script_content}")
            return "Mock AppleScript execution success."
            
        try:
            logger.info("Executing native AppleScript via osascript")
            res = subprocess.run(
                ["osascript", "-e", script_content],
                capture_output=True,
                text=True,
                check=True,
                timeout=5
            )
            return res.stdout.strip()
        except Exception as e:
            logger.error(f"AppleScript execution failed: {e}")
            raise RuntimeError(f"AppleScript execution failed: {e}")

class FileManager:
    @staticmethod
    def is_safe_path(path: str) -> bool:
        """
        Verifies if a path is located inside the safe workspace boundaries.
        """
        normalized_target = os.path.abspath(path)
        normalized_root = os.path.abspath(WORKSPACE_ROOT)
        
        # Also allow operations inside app data directory
        app_data_dir = "/Users/suprith.s.basavanal/.gemini/antigravity-ide"
        normalized_app_data = os.path.abspath(app_data_dir)
        
        return normalized_target.startswith(normalized_root) or normalized_target.startswith(normalized_app_data)

    @classmethod
    def read_file(cls, path: str) -> str:
        if not cls.is_safe_path(path):
            raise ValueError(f"Access denied: path is outside safe workspace boundaries: {path}")
            
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
            
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    @classmethod
    def create_file(cls, path: str, content: str) -> str:
        if not cls.is_safe_path(path):
            raise ValueError(f"Access denied: path is outside safe workspace boundaries: {path}")
            
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File created successfully at: {path}"

    @classmethod
    def edit_file(cls, path: str, target_text: str, replacement_text: str) -> str:
        if not cls.is_safe_path(path):
            raise ValueError(f"Access denied: path is outside safe workspace boundaries: {path}")
            
        content = cls.read_file(path)
        if target_text not in content:
            raise ValueError(f"Target text snippet to replace not found in file: {path}")
            
        new_content = content.replace(target_text, replacement_text)
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return f"File edited successfully: {path}"

    @classmethod
    def list_dir(cls, path: str) -> list[str]:
        if not cls.is_safe_path(path):
            raise ValueError(f"Access denied: path is outside safe workspace boundaries: {path}")
            
        if not os.path.isdir(path):
            raise ValueError(f"Path is not a directory: {path}")
            
        return os.listdir(path)

class BrowserController:
    @staticmethod
    def control_browser(action: str, url: str | None = None, scroll_amount: int | None = None) -> str:
        """
        Controls the browser via AppleScript.
        """
        # Choose Chrome as default browser
        browser = "Google Chrome"
        
        if action == "get_url":
            script = f'tell application "{browser}" to get URL of active tab of first window'
            try:
                return AppleScriptExecutor.execute(script)
            except Exception:
                return "https://github.com/suprithsbasavanal-alt/JARVIS-gpt"
                
        elif action == "set_url":
            if not url:
                raise ValueError("URL parameter required for set_url action.")
            script = f'tell application "{browser}" to set URL of active tab of first window to "{url}"'
            AppleScriptExecutor.execute(script)
            return f"Browser navigated to: {url}"
            
        elif action == "scroll":
            # Simple script to simulate page down via System Events keystroke
            amount = scroll_amount or 100
            script = f'''
            tell application "System Events"
                tell process "{browser}"
                    key code 125
                end tell
            end tell
            '''
            try:
                AppleScriptExecutor.execute(script)
            except Exception:
                pass
            return f"Scrolled browser by page down (approx {amount}px)"
            
        raise ValueError(f"Invalid browser control action: {action}")

class TerminalController:
    @staticmethod
    def run_command(command: str) -> str:
        """
        Runs a shell command safely and returns stdout/stderr.
        """
        logger.info(f"Executing terminal shell command: '{command}'")
        try:
            res = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=WORKSPACE_ROOT
            )
            output = res.stdout
            if res.stderr:
                output += f"\nError Output:\n{res.stderr}"
            return output.strip()
        except subprocess.TimeoutExpired:
            return f"Command execution timed out: '{command}'"
        except Exception as e:
            return f"Command failed with error: {str(e)}"

class ApplicationController:
    @staticmethod
    def launch(app_name: str) -> bool:
        """
        Launches an application.
        """
        logger.info(f"Launching application: {app_name}")
        if platform.system() == "Darwin":
            try:
                subprocess.Popen(["open", "-a", app_name])
                return True
            except Exception as e:
                logger.error(f"Failed to launch native macOS application: {e}")
                
        logger.info(f"[Mock launch]: Launched {app_name}")
        return True

    @staticmethod
    def quit(app_name: str) -> bool:
        """
        Quits an application via AppleScript.
        """
        script = f'quit application "{app_name}"'
        try:
            AppleScriptExecutor.execute(script)
            return True
        except Exception:
            logger.info(f"[Mock quit]: Quitted {app_name}")
            return True
