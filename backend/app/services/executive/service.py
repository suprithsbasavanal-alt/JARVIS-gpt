import logging
from datetime import datetime
from sqlalchemy.orm import Session
from backend.app.core.database import Goal, Task, Opportunity, Risk, EventStore

logger = logging.getLogger(__name__)

class ExecutiveService:
    """
    Core strategic reasoning intelligence. Analyzes user goals, monitors deadlines, 
    tracks project risks, flags opportunities, and scores task priorities.
    """
    
    @staticmethod
    def calculate_priority_score(task: Task, goal: Goal | None = None) -> float:
        """
        Compute a dynamic priority score for a task based on deadline proximity and weights.
        """
        base_score = 1.0
        if goal:
            base_score *= float(goal.priority_weight or 1.0)
            
        # Deadline calculation
        if task.due_date:
            time_left = task.due_date - datetime.utcnow()
            days_left = time_left.days + (time_left.seconds / 86400.0)
            if days_left <= 0:
                base_score += 10.0  # Overdue
            elif days_left <= 1.0:
                base_score += 5.0   # Critical deadline
            elif days_left <= 3.0:
                base_score += 2.5   # Near deadline
                
        return base_score

    @staticmethod
    def get_most_important_tasks(db: Session, limit: int = 3) -> list[dict]:
        """
        Priority Engine: Retrieve the top pending tasks sorted by dynamic priority score.
        """
        pending_tasks = db.query(Task).filter(Task.status.in_(["pending", "in_progress"])).all()
        scored_tasks = []
        
        for task in pending_tasks:
            goal = db.query(Goal).filter(Goal.id == task.goal_id).first() if task.goal_id else None
            score = ExecutiveService.calculate_priority_score(task, goal)
            scored_tasks.append((score, task))
            
        scored_tasks.sort(key=lambda x: x[0], reverse=True)
        
        results = []
        for score, task in scored_tasks[:limit]:
            results.append({
                "task_id": str(task.id),
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "priority_score": round(score, 2),
                "assigned_agent": task.assigned_agent,
                "due_date": task.due_date.isoformat() if task.due_date else None
            })
        return results

    @staticmethod
    def get_goals_behind_schedule(db: Session) -> list[dict]:
        """
        Goal Progress Engine: Detect goals that are past their deadline or have critical subtasks lagging.
        """
        active_goals = db.query(Goal).filter(Goal.status.in_(["pending", "in_progress"])).all()
        behind = []
        
        for goal in active_goals:
            is_behind = False
            reason = ""
            
            # 1. Deadline exceeded
            if goal.target_deadline and goal.target_deadline < datetime.utcnow():
                is_behind = True
                reason = "Goal target deadline has passed."
            else:
                # 2. Check if any subtask is overdue
                overdue_tasks = db.query(Task).filter(
                    Task.goal_id == goal.id,
                    Task.status.in_(["pending", "in_progress"]),
                    Task.due_date < datetime.utcnow()
                ).all()
                if overdue_tasks:
                    is_behind = True
                    reason = f"Contains {len(overdue_tasks)} overdue subtask(s)."
                    
            if is_behind:
                behind.append({
                    "goal_id": str(goal.id),
                    "title": goal.title,
                    "target_deadline": goal.target_deadline.isoformat() if goal.target_deadline else None,
                    "reason": reason
                })
        return behind

    @staticmethod
    def add_opportunity(
        db: Session,
        title: str,
        description: str | None = None,
        relevance_score: float = 0.00,
        source_url: str | None = None
    ) -> Opportunity:
        """
        Opportunity Engine: Register a newly identified opportunity.
        """
        logger.info(f"Registering opportunity: {title}")
        opp = Opportunity(
            title=title,
            description=description,
            relevance_score=relevance_score,
            source_url=source_url,
            status="identified"
        )
        db.add(opp)
        db.commit()
        db.refresh(opp)
        
        # Log event
        event = EventStore(
            event_type="opportunity_logged",
            payload={"id": str(opp.id), "title": title, "score": float(relevance_score)}
        )
        db.add(event)
        db.commit()
        
        return opp

    @staticmethod
    def get_active_opportunities(db: Session) -> list[Opportunity]:
        """
        Retrieve all identified active opportunities sorted by relevance score.
        """
        return db.query(Opportunity).filter(Opportunity.status == "identified").order_by(Opportunity.relevance_score.desc()).all()

    @staticmethod
    def add_risk(
        db: Session,
        title: str,
        description: str | None = None,
        severity: str = "medium",
        probability: float = 0.5,
        mitigation_plan: str | None = None
    ) -> Risk:
        """
        Risk Engine: Register a new strategic project risk.
        """
        logger.info(f"Registering risk: {title} ({severity})")
        risk = Risk(
            title=title,
            description=description,
            severity=severity,
            probability=probability,
            mitigation_plan=mitigation_plan,
            status="active"
        )
        db.add(risk)
        db.commit()
        db.refresh(risk)
        
        # Log event
        event = EventStore(
            event_type="risk_logged",
            payload={"id": str(risk.id), "title": title, "severity": severity}
        )
        db.add(event)
        db.commit()
        
        return risk

    @staticmethod
    def get_active_risks(db: Session) -> list[Risk]:
        """
        Retrieve all active risks sorted by probability.
        """
        return db.query(Risk).filter(Risk.status == "active").order_by(Risk.probability.desc()).all()
