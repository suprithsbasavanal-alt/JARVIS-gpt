import logging
import re
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from backend.app.core.database import AuditLog
from backend.app.services.automation.executor import FileManager

logger = logging.getLogger(__name__)

class SafetyGate:
    # Patterns for destructive or system-modifying terminal commands
    DANGEROUS_TERMINAL_PATTERNS = [
        r"\brm\b\s+-(?:r|f|rf|fr)\b", # rm -rf / rm -r
        r"\bsudo\b",                  # root access
        r"\bmv\b",                    # moves/renames (could move system folders)
        r"\bdd\b",                    # direct disk edits
        r"\bmkfs\b",                  # disk formatting
        r"\bchmod\b",                 # permissions change
        r"\bchown\b",                 # owner change
        r"\bshutdown\b",              # OS shutdown
        r"\breboot\b",                # OS reboot
        r"\bkill\b\s+-\d+",           # raw process termination
        r"\|\s*sh\b",                 # piping straight to shell (wget/curl)
        r"\|\s*bash\b"
    ]

    @classmethod
    def evaluate_risk(cls, tool_name: str, arguments: dict) -> tuple[bool, str]:
        """
        Determines if an action is high-risk.
        Returns a tuple: (is_high_risk, reason)
        """
        # 1. File path checks (any path must be inside workspace)
        for key in ["file_path", "directory_path"]:
            path = arguments.get(key)
            if path and not FileManager.is_safe_path(path):
                return True, f"Path '{path}' lies outside the safe workspace boundaries."

        # 2. Terminal command checks
        if tool_name == "terminal_cmd":
            cmd = arguments.get("command", "")
            for pattern in cls.DANGEROUS_TERMINAL_PATTERNS:
                if re.search(pattern, cmd):
                    return True, f"Terminal command '{cmd}' matches dangerous pattern: '{pattern}'"

        # 3. Explicit check for other critical actions if needed
        return False, "Action evaluated as safe."

class AuditSystem:
    @staticmethod
    def log_action(
        db: Session,
        action_type: str,
        command_payload: str,
        is_approved: bool = False
    ) -> AuditLog:
        """
        Creates a entry in action_audit_logs.
        """
        logger.info(f"Logging action to audit: {action_type} (Approved: {is_approved})")
        log = AuditLog(
            action_type=action_type,
            command_payload=command_payload,
            is_approved=is_approved,
            approved_at=datetime.utcnow() if is_approved else None
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def get_pending_audits(db: Session) -> list[AuditLog]:
        """
        Returns all pending action audit requests.
        """
        return db.query(AuditLog).filter(AuditLog.is_approved == False).all()

    @staticmethod
    def approve_audit(db: Session, audit_id: uuid.UUID) -> AuditLog | None:
        """
        Approves a pending audit action.
        """
        log = db.query(AuditLog).filter(AuditLog.id == audit_id).first()
        if log and not log.is_approved:
            log.is_approved = True
            log.approved_at = datetime.utcnow()
            db.commit()
            db.refresh(log)
            logger.info(f"Audit log ID {audit_id} approved.")
            return log
        return None
