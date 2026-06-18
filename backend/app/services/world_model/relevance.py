import logging
import json
from sqlalchemy.orm import Session
from backend.app.core.database import Goal, Project, Risk, Opportunity, EventStore

logger = logging.getLogger(__name__)

class RelevanceMatcher:
    @staticmethod
    def score_relevance(db: Session, title: str, description: str) -> float:
        """
        Calculates a relevance score (0.0 to 1.0) of a world event to the user's active context.
        Matches against active projects technologies and strategic goals.
        """
        text = f"{title} {description}".lower()
        
        # 1. Fetch user context
        projects = db.query(Project).all()
        goals = db.query(Goal).all()
        
        # If no active context set, return a baseline low relevance
        if not projects and not goals:
            return 0.1
            
        max_score = 0.0
        
        # 2. Check tech keyword match against projects
        for proj in projects:
            techs = proj.technologies or []
            # Technologies could be JSON list
            if isinstance(techs, str):
                try:
                    techs = json.loads(techs)
                except Exception:
                    techs = [techs]
            if not isinstance(techs, list):
                techs = []
                
            for t in techs:
                t_clean = str(t).lower().strip()
                if t_clean and t_clean in text:
                    # Technology match is high relevance
                    match_score = 0.9 if "vulnerability" in text or "cve" in text else 0.8
                    max_score = max(max_score, match_score)
                    
        # 3. Check keyword matches against goal titles
        for goal in goals:
            words = set(goal.title.lower().split())
            # filter short noise words
            words = {w for w in words if len(w) > 3}
            for w in words:
                if w in text:
                    max_score = max(max_score, 0.75)
                    
        return max_score

class StrategicAlertSystem:
    @staticmethod
    def process_and_alert(
        db: Session,
        world_event_id: str,
        title: str,
        description: str,
        category: str,
        relevance_score: float,
        source_url: str | None = None
    ) -> dict | None:
        """
        Generates and saves active Risks or Opportunities based on highly relevant world events.
        """
        if relevance_score < 0.7:
            return None
            
        logger.info(f"Strategic alert triggered! Highly relevant event: '{title}' (Score: {relevance_score})")
        
        # 1. Create corresponding Risk or Opportunity
        alert_item = None
        if category == "Security Vulnerability":
            # Add to Risks table
            risk = Risk(
                title=f"Security Advisory: {title}",
                description=description,
                severity="critical" if "rce" in title.lower() or "critical" in title.lower() else "high",
                probability=0.9,
                mitigation_plan=f"Review dependency vulnerability logs for matching assets at {source_url}.",
                status="active"
            )
            db.add(risk)
            db.commit()
            db.refresh(risk)
            alert_item = {
                "type": "risk",
                "id": str(risk.id),
                "title": risk.title,
                "severity": risk.severity
            }
        elif category in ["AI Release", "Tech Trend"]:
            # Add to Opportunities table
            opp = Opportunity(
                title=f"Emerging Tech Opportunity: {title}",
                description=description,
                relevance_score=relevance_score,
                source_url=source_url,
                status="identified"
            )
            db.add(opp)
            db.commit()
            db.refresh(opp)
            alert_item = {
                "type": "opportunity",
                "id": str(opp.id),
                "title": opp.title,
                "relevance": opp.relevance_score
            }
            
        # 2. Log strategic alert event to Event Store
        if alert_item:
            event = EventStore(
                event_type="strategic_alert",
                payload={
                    "world_event_id": world_event_id,
                    "alert_type": alert_item["type"],
                    "alert_id": alert_item["id"],
                    "relevance_score": relevance_score
                }
            )
            db.add(event)
            db.commit()
            
        return alert_item
