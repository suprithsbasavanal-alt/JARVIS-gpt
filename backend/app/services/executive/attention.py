import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.app.core.database import AttentionLog

logger = logging.getLogger(__name__)

class AttentionAllocationEngine:
    """
    Computes aggregated analytics on focus budgets, compares target allocations, 
    and highlights time allocation leakage.
    """
    
    @staticmethod
    def get_attention_summary(db: Session, timeframe_hours: int = 24) -> dict:
        """
        Analyze attention logs over a specific timeframe window.
        """
        time_limit = datetime.utcnow() - timedelta(hours=timeframe_hours)
        logs = db.query(AttentionLog).filter(AttentionLog.timestamp >= time_limit).all()
        
        category_seconds = {}
        total_seconds = 0
        
        for log in logs:
            cat = log.category or "uncategorized"
            category_seconds[cat] = category_seconds.get(cat, 0.0) + log.time_spent_seconds
            total_seconds += log.time_spent_seconds
            
        # Convert to minutes for readable reports
        category_minutes = {cat: round(sec / 60.0, 1) for cat, sec in category_seconds.items()}
        
        coding_time = category_seconds.get("coding", 0.0)
        distraction_time = category_seconds.get("distraction", 0.0)
        
        focus_efficiency = 100.0
        if (coding_time + distraction_time) > 0:
            focus_efficiency = (coding_time / (coding_time + distraction_time)) * 100.0
            
        # Evaluate alignment state
        status = "aligned"
        if distraction_time > coding_time:
            status = "distracted/scattered"
            
        return {
            "timeframe_hours": timeframe_hours,
            "total_logged_minutes": round(total_seconds / 60.0, 1),
            "category_breakdown_minutes": category_minutes,
            "focus_efficiency_percentage": round(focus_efficiency, 1),
            "allocation_alignment_status": status
        }
