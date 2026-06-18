import logging
import json
import uuid
from sqlalchemy.orm import Session
from backend.app.services.automation.registry import ToolRegistry
from backend.app.services.automation.safety import SafetyGate, AuditSystem
from backend.app.services.automation.executor import (
    FileManager,
    BrowserController,
    TerminalController,
    ApplicationController
)

logger = logging.getLogger(__name__)

class AutomationService:
    @classmethod
    def execute_action(
        cls,
        db: Session,
        tool_name: str,
        arguments: dict,
        force_execute: bool = False
    ) -> dict:
        """
        Validates, gates, logs, and executes an automation tool action.
        """
        # 1. Validate tool schema
        tool = ToolRegistry.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Unknown automation tool: '{tool_name}'")
            
        # 2. Check Safety Gate
        is_high_risk, reason = SafetyGate.evaluate_risk(tool_name, arguments)
        
        # Format payload for audit logging
        payload_str = json.dumps({
            "tool_name": tool_name,
            "arguments": arguments
        })
        
        # 3. If high-risk and not explicitly approved/forced, put in approval queue
        if is_high_risk and not force_execute:
            logger.warning(f"High-risk action blocked by safety gate. ID queued. Reason: {reason}")
            log = AuditSystem.log_action(
                db=db,
                action_type=tool_name,
                command_payload=payload_str,
                is_approved=False
            )
            return {
                "status": "pending_approval",
                "audit_id": str(log.id),
                "reason": reason
            }
            
        # 4. Action is safe or pre-approved, execute it
        log = AuditSystem.log_action(
            db=db,
            action_type=tool_name,
            command_payload=payload_str,
            is_approved=True
        )
        
        output = ""
        try:
            if tool_name == "launch_app":
                app_name = arguments.get("app_name")
                success = ApplicationController.launch(app_name)
                output = f"Application launch triggered: {app_name}" if success else f"Failed to launch app: {app_name}"
                
            elif tool_name == "read_file":
                file_path = arguments.get("file_path")
                output = FileManager.read_file(file_path)
                
            elif tool_name == "create_file":
                file_path = arguments.get("file_path")
                content = arguments.get("content", "")
                output = FileManager.create_file(file_path, content)
                
            elif tool_name == "edit_file":
                file_path = arguments.get("file_path")
                target_text = arguments.get("target_text")
                replacement_text = arguments.get("replacement_text")
                output = FileManager.edit_file(file_path, target_text, replacement_text)
                
            elif tool_name == "list_dir":
                dir_path = arguments.get("directory_path")
                files = FileManager.list_dir(dir_path)
                output = json.dumps(files)
                
            elif tool_name == "terminal_cmd":
                command = arguments.get("command")
                output = TerminalController.run_command(command)
                
            elif tool_name == "browser_control":
                action = arguments.get("action")
                url = arguments.get("url")
                scroll_amount = arguments.get("scroll_amount")
                output = BrowserController.control_browser(action, url, scroll_amount)
                
        except Exception as e:
            logger.error(f"Error executing tool '{tool_name}': {e}", exc_info=True)
            output = f"Error during tool execution: {str(e)}"
            return {
                "status": "failed",
                "output": output
            }
            
        return {
            "status": "success",
            "output": output
        }

    @classmethod
    def execute_pending_action(cls, db: Session, audit_id: uuid.UUID) -> dict:
        """
        Approves and executes a previously blocked high-risk action.
        """
        # Approve in audit logs
        log = AuditSystem.approve_audit(db, audit_id)
        if not log:
            raise ValueError(f"No pending or unapproved audit log found for ID: {audit_id}")
            
        # Parse payload details
        payload = json.loads(log.command_payload)
        tool_name = payload["tool_name"]
        arguments = payload["arguments"]
        
        logger.info(f"Re-executing approved high-risk tool: {tool_name}")
        
        # Execute tool forcing execution bypass
        return cls.execute_action(
            db=db,
            tool_name=tool_name,
            arguments=arguments,
            force_execute=True
        )
