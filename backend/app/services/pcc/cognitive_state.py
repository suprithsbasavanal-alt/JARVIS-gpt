import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.app.core.database import AttentionLog, Project

logger = logging.getLogger(__name__)

class CognitiveStateService:
    """
    Computes real-time cognitive state, user attention levels, focus targets, and active projects
    by aggregating logs from active OS window titles and application categories.
    """
    
    @staticmethod
    def log_attention_activity(
        db: Session,
        active_application: str,
        active_window_title: str,
        time_spent_seconds: float,
        category: str = "coding"
    ) -> AttentionLog:
        """
        Record a new attention segment.
        """
        logger.info(f"Logging focus activity: {active_application} - {active_window_title}")
        log = AttentionLog(
            active_application=active_application,
            active_window_title=active_window_title,
            time_spent_seconds=time_spent_seconds,
            category=category,
            timestamp=datetime.utcnow()
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def get_active_cognitive_state(db: Session) -> dict:
        """
        Determine the user's active focus target, computed cognitive load, and attention drift.
        """
        # 1. Fetch recent attention segments in the last 15 minutes
        time_limit = datetime.utcnow() - timedelta(minutes=15)
        recent_logs = db.query(AttentionLog).filter(AttentionLog.timestamp >= time_limit).all()
        
        if not recent_logs:
            return {
                "active_application": "Unknown",
                "active_window_title": "Idle",
                "active_project": None,
                "cognitive_load": "low",
                "attention_drift_alert": False
            }
            
        # 2. Analyze dominant application and window
        app_durations = {}
        total_distraction = 0
        total_time = 0
        latest_log = recent_logs[-1]
        
        for log in recent_logs:
            app_durations[log.active_application] = app_durations.get(log.active_application, 0) + log.time_spent_seconds
            total_time += log.time_spent_seconds
            if log.category == "distraction":
                total_distraction += log.time_spent_seconds
                
        dominant_app = max(app_durations, key=app_durations.get)
        
        # 3. Heuristic project recognition from window titles/active paths
        active_project = None
        all_projects = db.query(Project).all()
        combined_titles = " ".join([l.active_window_title or "" for l in recent_logs]).lower()
        
        for project in all_projects:
            if project.name.lower() in combined_titles or (project.workspace_path and project.workspace_path.lower() in combined_titles):
                active_project = project.name
                break
                
        # 4. Compute attention drift alert (if distracted > 40% of the active window)
        drift_alert = False
        if total_time > 0 and (total_distraction / total_time) > 0.40:
            drift_alert = True
            
        # 5. Cognitive load estimation based on recent switching frequency
        switching_frequency = len(set(l.active_application for l in recent_logs))
        cognitive_load = "normal"
        if switching_frequency > 4:
            cognitive_load = "high (fractured focus)"
        elif switching_frequency <= 1:
            cognitive_load = "high (deep flow)"
            
        return {
            "active_application": dominant_app,
            "active_window_title": latest_log.active_window_title,
            "active_project": active_project or "General Tasks",
            "cognitive_load": cognitive_load,
            "attention_drift_alert": drift_alert
        }
