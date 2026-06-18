import logging
from sqlalchemy.orm import Session
from backend.app.services.executive.service import ExecutiveService
from backend.app.services.executive.attention import AttentionAllocationEngine
from backend.app.services.pcc.cognitive_state import CognitiveStateService

logger = logging.getLogger(__name__)

class BriefingGenerator:
    """
    Synthesizes strategic reports, daily briefs, and retrospective reviews 
    to outline current attention targets and system health.
    """
    
    @staticmethod
    def generate_daily_briefing(db: Session) -> str:
        """
        Build the consolidated strategic daily briefing.
        """
        logger.info("Generating Daily Briefing...")
        
        # 1. Focus & Cognitive State
        state = CognitiveStateService.get_active_cognitive_state(db)
        
        # 2. Priorities
        priorities = ExecutiveService.get_most_important_tasks(db, limit=3)
        priority_lines = []
        for p in priorities:
            due_str = f" (Due: {p['due_date']})" if p['due_date'] else ""
            priority_lines.append(f"- **{p['title']}** - Status: `{p['status']}` | Priority Weight: {p['priority_score']}{due_str}")
        if not priority_lines:
            priority_lines = ["*No active pending tasks. Ready to allocate new goals.*"]
            
        # 3. Behind schedule
        behind = ExecutiveService.get_goals_behind_schedule(db)
        behind_lines = [f"- **{g['title']}**: {g['reason']}" for g in behind]
        if not behind_lines:
            behind_lines = ["*All goals are currently on track.*"]
            
        # 4. Opportunities
        opps = ExecutiveService.get_active_opportunities(db)
        opp_lines = [f"- **{o.title}** (Relevance: {o.relevance_score})" for o in opps[:3]]
        if not opp_lines:
            opp_lines = ["*No new opportunities flagged.*"]
            
        # 5. Risks
        risks = ExecutiveService.get_active_risks(db)
        risk_lines = [f"- **{r.title}** (Severity: `{r.severity}` | Probability: {r.probability})" for r in risks[:3]]
        if not risk_lines:
            risk_lines = ["*No critical risks registered.*"]
            
        # Compile Markdown
        briefing = f"""# JARVIS Daily Strategic Briefing

## 1. Cognitive State & Focus
* **Active Project Target**: {state['active_project']}
* **Dominant Application**: {state['active_application']}
* **Window Title**: {state['active_window_title']}
* **Estimated Cognitive Load**: `{state['cognitive_load']}`
* **Attention Drift Alert**: {"⚠️ Drift Detected (Check Distractions)" if state['attention_drift_alert'] else "✅ Aligned Flow State"}

## 2. Strategic Priorities (MITs)
{chr(10).join(priority_lines)}

## 3. Goals & Progress Alerts
{chr(10).join(behind_lines)}

## 4. Operational Risk Registry
{chr(10).join(risk_lines)}

## 5. Emerging Opportunity Vector
{chr(10).join(opp_lines)}
"""
        return briefing.strip()

    @staticmethod
    def generate_weekly_review(db: Session) -> str:
        """
        Build the retrospective focus allocation review for the last 7 days.
        """
        logger.info("Generating Weekly Review...")
        
        # 1. Fetch focus metrics for last 168 hours (7 days)
        summary = AttentionAllocationEngine.get_attention_summary(db, timeframe_hours=168)
        
        breakdown_lines = []
        for cat, mins in summary["category_breakdown_minutes"].items():
            breakdown_lines.append(f"- **{cat.capitalize()}**: {mins} minutes")
        if not breakdown_lines:
            breakdown_lines = ["*No activity logs recorded.*"]
            
        review = f"""# JARVIS Weekly Retrospective Review

## 1. Focus Time Allocation
* **Total Logged Activity**: {summary['total_logged_minutes']} minutes
* **Focus Efficiency Rating**: {summary['focus_efficiency_percentage']}%
* **Time Alignment Status**: `{summary['allocation_alignment_status']}`

### Category Breakdown
{chr(10).join(breakdown_lines)}

## 2. Cognitive Performance Notes
* Weekly efficiency score is {"excellent (flow state achieved)" if summary['focus_efficiency_percentage'] > 75 else "fragmented (high context-switching)"}.
* Keep distractions minimized to align allocations with strategic objectives.
"""
        return review.strip()
