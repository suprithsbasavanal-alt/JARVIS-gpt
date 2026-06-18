import logging
from datetime import datetime, time
from sqlalchemy.orm import Session
from backend.app.core.database import Task, Message, ActionAuditLog, KnowledgeNode
from backend.app.services.pcc.service import PCCService
from backend.app.services.memory.service import MemoryService
from backend.app.agents.critic import CriticAgent

logger = logging.getLogger(__name__)

class AgentCriticService:
    """
    Orchestrates Cycle 4 Agent Self-Evaluation logic.
    Analyzes agent executions and saves criticisms to the Personal Knowledge Graph.
    """

    @staticmethod
    def evaluate_agent_performance(db: Session) -> dict:
        """
        Gathers daily execution metrics, runs CriticAgent, saves graph nodes/edges,
        and logs critic feedback to long-term memory.
        """
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        node_id = f"evaluation_{date_str.replace('-', '_')}"
        logger.info(f"Evaluating agent performance for {date_str}...")

        # 1. Fetch completed/pending tasks and audit logs
        start_of_today = datetime.combine(datetime.utcnow().date(), time.min)
        tasks = db.query(Task).all()
        messages = db.query(Message).filter(Message.created_at >= start_of_today).all()
        audit_logs = db.query(ActionAuditLog).filter(ActionAuditLog.created_at >= start_of_today).all()

        # 2. Compile execution metrics
        safety_failures = len([l for l in audit_logs if not l.is_approved])
        execution_metrics = {
            "date": date_str,
            "task_count": len(tasks),
            "messages_count": len(messages),
            "audit_logs_count": len(audit_logs),
            "safety_failures_count": safety_failures
        }

        # 3. Trigger Critic Agent
        agent = CriticAgent()
        evaluation_result = agent.evaluate_performance(execution_metrics)

        # 4. Establish user profile node if missing
        PCCService.upsert_node(db, "user_me", "user", "Owner Profile")

        # 5. Save evaluation node to Personal Knowledge Graph
        db_node = PCCService.upsert_node(
            db=db,
            node_id=node_id,
            node_type="evaluation",
            label=f"Evaluation - {date_str}",
            properties=evaluation_result
        )

        # 6. Connect edge: user_me --[EVALUATED_AGENTS]--> evaluation_node
        PCCService.upsert_edge(
            db=db,
            source_node_id="user_me",
            relationship_type="EVALUATED_AGENTS",
            target_node_id=node_id
        )

        # 7. Log critic corrective feedback to memory if performance is subpar (< 7.0)
        grades = [
            evaluation_result.get("planning_grade", 10.0),
            evaluation_result.get("research_grade", 10.0),
            evaluation_result.get("automation_grade", 10.0),
            evaluation_result.get("memory_grade", 10.0)
        ]
        
        is_subpar = any(grade < 7.0 for grade in grades)
        if is_subpar:
            feedback_key = f"critic_feedback_{date_str.replace('-', '_')}"
            MemoryService.create_or_update_memory(
                db=db,
                entity_key=feedback_key,
                entity_value=evaluation_result.get("overall_feedback", "Distilled agent prompt adjustments recommended."),
                category="critic",
                salience_score=3.0
            )
            logger.info(f"Subpar performance detected. Corrective critic feedback written to memory.")

        db.commit()
        return {
            "node_id": node_id,
            "date": date_str,
            "evaluation": evaluation_result
        }

    @staticmethod
    def get_evaluation_history(db: Session, limit: int = 10) -> list[dict]:
        """
        Retrieves recent agent evaluations from knowledge nodes.
        """
        nodes = db.query(KnowledgeNode).filter(
            KnowledgeNode.node_type == "evaluation"
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
