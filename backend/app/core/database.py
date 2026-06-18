import uuid
from datetime import datetime
from sqlalchemy import create_engine, Column, String, DateTime, Text, ForeignKey, Boolean, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from backend.app.core.config import settings

Base = declarative_base()

# Try to connect to PostgreSQL. If it fails, fall back to SQLite.
db_url = settings.DATABASE_URL
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

try:
    engine = create_engine(db_url, pool_pre_ping=True)
    with engine.connect() as conn:
        pass
except Exception:
    import os
    sqlite_db = os.path.join(os.path.dirname(__file__), "jarvis.db")
    db_url = f"sqlite:///{sqlite_db}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 1. Core User Profile
class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    memories = relationship("Memory", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")

# 2. Strategic Goals & Targets
class Goal(Base):
    __tablename__ = "goals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="pending")  # 'pending', 'in_progress', 'completed', 'failed'
    target_deadline = Column(DateTime(timezone=True), nullable=True)
    priority_weight = Column(Float, default=1.00)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    user = relationship("User", back_populates="goals")
    tasks = relationship("Task", back_populates="goal", cascade="all, delete-orphan")

# 3. Active Codebase Projects
class Project(Base):
    __tablename__ = "projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    name = Column(String(255), nullable=False)
    workspace_path = Column(String(512), nullable=False, unique=True)
    technologies = Column(JSON, nullable=True)  # Store as JSON list of strings
    priority_level = Column(String(50), default="normal")  # 'low', 'normal', 'high', 'critical'
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    user = relationship("User", back_populates="projects")
    tasks = relationship("Task", back_populates="project")

# 4. Goal Milestones and Subtasks
class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    goal_id = Column(UUID(as_uuid=True), ForeignKey("goals.id", ondelete="CASCADE"), nullable=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="pending")  # 'pending', 'in_progress', 'completed', 'failed'
    assigned_agent = Column(String(100), nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True)
    
    goal = relationship("Goal", back_populates="tasks")
    project = relationship("Project", back_populates="tasks")
    subtasks = relationship("Task", cascade="all, delete-orphan")

# 5. Factual Belief & Consolidated Preference Store
class Memory(Base):
    __tablename__ = "memories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    entity_key = Column(String(255), unique=True, nullable=False)
    entity_value = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)  # 'preference', 'lifestyle', 'habit'
    salience_score = Column(Float, default=1.00)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="memories")

# 6. Conversation Headers
class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    title = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

# 7. Episodic Chat Messages
class Message(Base):
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    sender = Column(String(50), nullable=False)  # 'user', 'jarvis', 'system'
    content = Column(Text, nullable=False)
    thought_trace = Column(Text, nullable=True)
    attachments = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    conversation = relationship("Conversation", back_populates="messages")

# 8. Personal Knowledge Graph Nodes
class KnowledgeNode(Base):
    __tablename__ = "knowledge_nodes"
    
    id = Column(String(100), primary_key=True)  # Unique entity name (e.g. 'tech_rust')
    node_type = Column(String(100), nullable=False)  # 'skill', 'opportunity', 'project', 'goal'
    label = Column(String(255), nullable=False)
    properties = Column(JSON, nullable=True)
    salience_score = Column(Float, default=1.00)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

# 9. Personal Knowledge Graph Edges
class KnowledgeEdge(Base):
    __tablename__ = "knowledge_edges"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_node_id = Column(String(100), ForeignKey("knowledge_nodes.id", ondelete="CASCADE"), nullable=False)
    relationship_type = Column(String(100), nullable=False)  # 'REQUIRES', 'BELONGS_TO', 'WORKS_ON'
    target_node_id = Column(String(100), ForeignKey("knowledge_nodes.id", ondelete="CASCADE"), nullable=False)
    weight = Column(Float, default=1.00)

# 10. Active Opportunities
class Opportunity(Base):
    __tablename__ = "opportunities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    relevance_score = Column(Float, default=0.00)
    source_url = Column(String(512), nullable=True)
    status = Column(String(50), default="identified")  # 'identified', 'ignored', 'pursued'
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

# 11. Active Risks
class Risk(Base):
    __tablename__ = "risks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String(50), nullable=True)  # 'low', 'medium', 'high', 'critical'
    probability = Column(Float, default=0.00)
    mitigation_plan = Column(Text, nullable=True)
    status = Column(String(50), default="active")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

# 12. World Scrape Events
class WorldEvent(Base):
    __tablename__ = "world_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)  # 'AI Release', 'Vulnerability', 'Market'
    event_payload = Column(JSON, nullable=True)
    source_url = Column(String(512), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

# 13. Attention Logs (Focus & Activity)
class AttentionLog(Base):
    __tablename__ = "attention_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    active_application = Column(String(100), nullable=False)
    active_window_title = Column(String(255), nullable=True)
    time_spent_seconds = Column(Float, nullable=False)
    category = Column(String(100), nullable=True)  # 'coding', 'browsing', 'distraction'
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow)

# 14. Action Audit Log Gates
class ActionAuditLog(Base):
    __tablename__ = "action_audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action_type = Column(String(100), nullable=False)  # 'shell_cmd', 'file_write', 'app_launch'
    command_payload = Column(Text, nullable=False)
    is_approved = Column(Boolean, default=False)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

# 15. Unified Event Store (Change #2)
class EventStore(Base):
    __tablename__ = "events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

# 16. Agent Registry (Change #3)
class AgentRegistry(Base):
    __tablename__ = "agent_registry"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_name = Column(String(100), nullable=False, unique=True)
    capabilities = Column(JSON, nullable=True)  # List of string capabilities
    status = Column(String(50), default="active")  # 'active', 'paused', 'deprecated'
    version = Column(String(50), default="1.0.0")
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

# Keep AuditLog alias for backward compatibility
AuditLog = ActionAuditLog
