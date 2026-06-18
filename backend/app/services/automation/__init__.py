from backend.app.services.automation.registry import ToolRegistry
from backend.app.services.automation.executor import (
    AppleScriptExecutor,
    FileManager,
    BrowserController,
    TerminalController,
    ApplicationController
)
from backend.app.services.automation.safety import SafetyGate, AuditSystem
from backend.app.services.automation.service import AutomationService
