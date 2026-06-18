import logging
from datetime import datetime, timedelta, time
from sqlalchemy.orm import Session
from backend.app.core.database import Goal, Task, Risk, Opportunity, Message, KnowledgeNode
from backend.app.services.pcc.cognitive_state import CognitiveStateService
from backend.app.services.executive.attention import AttentionAllocationEngine
from backend.app.services.pcc.service import PCCService
from backend.app.services.memory.service import MemoryService
from backend.app.agents.reflection import ReflectionAgent

logger = logging.getLogger(__name__)

class ReflectionService:
    """
    Orchestrates Cycle 3 Self-Improvement logic.
    Aggregates user telemetry daily and calculates actionable reflections.
    """

    @staticmethod
    def generate_reflection(db: Session) -> dict:
        """
        Gathers daily telemetry, triggers ReflectionAgent, saves graph/memories,
        and dynamically updates goal priority weights.
        """
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        node_id = f"reflection_{date_str.replace('-', '_')}"
        logger.info(f"Generating reflection report for {date_str}...")

        # 1. Fetch cognitive state & active application context
        try:
            cognitive_state = CognitiveStateService.get_active_cognitive_state(db)
        except Exception as e:
            logger.warning(f"Failed to fetch cognitive state: {e}")
            cognitive_state = {"active_project": "None", "active_application": "None", "active_window_title": "None", "cognitive_load": "low", "attention_drift_alert": False}

        # 2. Fetch completed and pending tasks
        # Completed today: task completed_at is today
        start_of_today = datetime.combine(datetime.utcnow().date(), time.min)
        completed_tasks = db.query(Task).filter(
            Task.status == "completed",
            Task.completed_at >= start_of_today
        ).all()
        pending_tasks = db.query(Task).filter(Task.status == "pending").all()

        # 3. Fetch attention/efficiency analytics (24 hours)
        try:
            attention_summary = AttentionAllocationEngine.get_attention_summary(db, timeframe_hours=24)
        except Exception as e:
            logger.warning(f"Failed to fetch attention summary: {e}")
            attention_summary = {"focus_efficiency_percentage": 100.0, "allocation_alignment_status": "aligned", "category_breakdown_minutes": {}}

        # 4. Fetch goals, risks, opportunities
        active_goals = db.query(Goal).filter(Goal.status != "completed").all()
        active_risks = db.query(Risk).filter(Risk.status == "active").all()
        active_opps = db.query(Opportunity).filter(Opportunity.status == "identified").all()

        # 5. Compile telemetry package
        telemetry = {
            "date": date_str,
            "active_project": cognitive_state.get("active_project"),
            "active_application": cognitive_state.get("active_application"),
            "cognitive_load": cognitive_state.get("cognitive_load"),
            "completed_tasks": [{"title": t.title, "description": t.description} for t in completed_tasks],
            "pending_tasks": [{"title": t.title, "description": t.description} for t in pending_tasks],
            "focus_efficiency": attention_summary.get("focus_efficiency_percentage"),
            "attention_status": attention_summary.get("allocation_alignment_status"),
            "category_breakdown": attention_summary.get("category_breakdown_minutes"),
            "active_goals": [{"id": str(g.id), "title": g.title, "priority_weight": g.priority_weight} for g in active_goals],
            "active_risks": [r.title for r in active_risks],
            "active_opportunities": [o.title for o in active_opps]
        }

        # 6. Run LLM/Heuristic Reflection Agent
        agent = ReflectionAgent()
        reflection_result = agent.generate_reflection_report(telemetry)

        # 7. Establish User node if missing
        PCCService.upsert_node(db, "user_me", "user", "Owner Profile")

        # 8. Save Reflection node in Personal Knowledge Graph
        db_node = PCCService.upsert_node(
            db=db,
            node_id=node_id,
            node_type="reflection",
            label=f"Reflection - {date_str}",
            properties=reflection_result
        )

        # 9. Connect edge: user_me --[REFLECTED_ON]--> reflection_node
        PCCService.upsert_edge(
            db=db,
            source_node_id="user_me",
            relationship_type="REFLECTED_ON",
            target_node_id=node_id
        )

        # 10. Link reflection to active project if valid
        active_proj = cognitive_state.get("active_project")
        if active_proj and active_proj != "None":
            proj_node_id = f"project_{active_proj.lower()}"
            proj_exists = db.query(KnowledgeNode).filter(KnowledgeNode.id == proj_node_id).first()
            if proj_exists:
                PCCService.upsert_edge(
                    db=db,
                    source_node_id=node_id,
                    relationship_type="REFLECTS_PROJECT",
                    target_node_id=proj_node_id
                )

        # 11. Save adjustments to relational memories
        MemoryService.create_or_update_memory(
            db=db,
            entity_key=f"reflection_insights_{date_str.replace('-', '_')}",
            entity_value=reflection_result.get("adjustments", ""),
            category="reflection",
            salience_score=2.0
        )

        # 12. Dynamic priorities adjustment (overdue goals reinforcement)
        # If any goal matches keywords in what_failed or adjustments, increment priority weight
        failed_text = reflection_result.get("what_failed", "").lower()
        adjustments_text = reflection_result.get("adjustments", "").lower()
        
        for goal in active_goals:
            # Check for title keyword matches
            goal_title_lower = goal.title.lower()
            should_reinforce = False
            
            # Simple keyword matching heuristic
            words = [w for w in goal_title_lower.split() if len(w) > 3]
            for w in words:
                if w in failed_text or w in adjustments_text:
                    should_reinforce = True
                    break
                    
            if should_reinforce:
                old_weight = goal.priority_weight or 1.0
                # Reinforce weight by +0.1, capped at 3.0
                new_weight = min(old_weight + 0.1, 3.0)
                goal.priority_weight = new_weight
                logger.info(f"Reinforced goal priority weight for '{goal.title}': {old_weight} -> {new_weight}")
        
        db.commit()
        return {
            "node_id": node_id,
            "date": date_str,
            "report": reflection_result
        }

    @staticmethod
    def get_reflection_history(db: Session, limit: int = 10) -> list[dict]:
        """
        Retrieves recent reflections stored in the knowledge nodes.
        """
        nodes = db.query(KnowledgeNode).filter(
            KnowledgeNode.node_type == "reflection"
        ).order_by(KnowledgeNode.updated_at.desc()).limit(limit).all()
        
        history = []
        for node in nodes:
            history.append({
                "id": node.id,
                "label": node.label,
                "properties": node.properties,
                "updated_at": node.updated_at.isoformat()
            })
        return history
