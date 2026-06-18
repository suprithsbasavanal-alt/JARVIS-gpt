import logging

logger = logging.getLogger(__name__)

class ToolRegistry:
    TOOLS = {
        "launch_app": {
            "name": "launch_app",
            "description": "Opens or launches a desktop application on macOS.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "The name of the application (e.g. 'Safari', 'VS Code', 'Notes')."}
                },
                "required": ["app_name"]
            }
        },
        "read_file": {
            "name": "read_file",
            "description": "Reads the content of a text file within safe workspace directories.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Absolute path to the target text file."}
                },
                "required": ["file_path"]
            }
        },
        "create_file": {
            "name": "create_file",
            "description": "Creates a new text file at the specified path with the provided content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Absolute path to create the new file."},
                    "content": {"type": "string", "description": "The text content to write to the file."}
                },
                "required": ["file_path", "content"]
            }
        },
        "edit_file": {
            "name": "edit_file",
            "description": "Replaces a specific substring (target_text) with replacement_text inside a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Absolute path to the target file."},
                    "target_text": {"type": "string", "description": "The exact block of text inside the file to replace."},
                    "replacement_text": {"type": "string", "description": "The new content to put in place of target_text."}
                },
                "required": ["file_path", "target_text", "replacement_text"]
            }
        },
        "list_dir": {
            "name": "list_dir",
            "description": "Lists the files and folders inside the specified directory path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory_path": {"type": "string", "description": "Absolute path to the directory to list."}
                },
                "required": ["directory_path"]
            }
        },
        "terminal_cmd": {
            "name": "terminal_cmd",
            "description": "Executes a shell command on macOS terminal. Destructive or system-modifying commands require approval.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The shell command line string to run (e.g. 'git status', 'ls -la')."}
                },
                "required": ["command"]
            }
        },
        "browser_control": {
            "name": "browser_control",
            "description": "Controls active browser tab (Safari or Chrome) using AppleScript.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["get_url", "set_url", "scroll"], "description": "Action type to run."},
                    "url": {"type": "string", "description": "URL to navigate to (required for set_url)."},
                    "scroll_amount": {"type": "integer", "description": "Amount of pixels to scroll (required for scroll action)."}
                },
                "required": ["action"]
            }
        }
    }

    @classmethod
    def get_tool_schemas(cls) -> list[dict]:
        """
        Returns all registered tool schemas.
        """
        return list(cls.TOOLS.values())

    @classmethod
    def get_tool(cls, name: str) -> dict | None:
        """
        Returns the schema for a specific tool.
        """
        return cls.TOOLS.get(name)
