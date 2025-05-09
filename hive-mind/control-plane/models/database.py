from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Table, Enum, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import Dict, List, Optional
import enum
import uuid
from datetime import datetime

from models.agents import AgentRole, AgentTier

Base = declarative_base()

# Association tables for many-to-many relationships
team_agent_association = Table(
    'team_agent_association',
    Base.metadata,
    Column('team_id', String, ForeignKey('teams.id'), primary_key=True),
    Column('agent_id', String, ForeignKey('agents.id'), primary_key=True)
)

project_user_association = Table(
    'project_user_association',
    Base.metadata,
    Column('project_id', String, ForeignKey('projects.id'), primary_key=True),
    Column('user_id', String, ForeignKey('users.id'), primary_key=True),
    Column('role', String, nullable=False)  # Owner, Editor, Viewer, etc.
)

task_tag_association = Table(
    'task_tag_association',
    Base.metadata,
    Column('task_id', String, ForeignKey('tasks.id'), primary_key=True),
    Column('tag_id', String, ForeignKey('tags.id'), primary_key=True)
)

class UserType(str, enum.Enum):
    HUMAN = "human"
    AGENT = "agent"

class TaskStatus(str, enum.Enum):
    CREATED = "created"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    WAITING_FOR_REVIEW = "waiting_for_review"
    REVISION_NEEDED = "revision_needed"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"

class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class User(Base):
    __tablename__ = 'users'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    user_type = Column(Enum(UserType), default=UserType.HUMAN, nullable=False)
    avatar_url = Column(String)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    tasks = relationship("Task", foreign_keys="Task.assigned_to", back_populates="assignee")
    teams = relationship("Team", secondary=lambda: project_user_association)
    projects = relationship("Project", secondary=lambda: project_user_association)
    comments = relationship("TaskComment", back_populates="author")
    
    def __repr__(self):
        return f"<User {self.username}>"

class Agent(Base):
    __tablename__ = 'agents'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    role = Column(Enum(AgentRole), nullable=False)
    model = Column(String, nullable=False)
    tier = Column(Enum(AgentTier), nullable=False, default=AgentTier.STANDARD)
    temperature = Column(Float, default=0.7)
    token_limit = Column(Integer, default=4096)
    use_prompt_engineering = Column(Boolean, default=False)
    custom_settings = Column(JSON, default={})
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    tasks = relationship("Task", foreign_keys="Task.assigned_to", back_populates="assignee")
    teams = relationship("Team", secondary=lambda: team_agent_association, back_populates="agents")
    
    def __repr__(self):
        return f"<Agent {self.name} ({self.role})>"

class Team(Base):
    __tablename__ = 'teams'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text)
    workspace_id = Column(String, ForeignKey('workspaces.id'))
    budget = Column(Float)
    created_by = Column(String, ForeignKey('users.id'))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    agents = relationship("Agent", secondary=lambda: team_agent_association, back_populates="teams")
    workspace = relationship("Workspace", back_populates="teams")
    tasks = relationship("Task", back_populates="team")
    
    def __repr__(self):
        return f"<Team {self.name}>"

class Workspace(Base):
    __tablename__ = 'workspaces'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text)
    created_by = Column(String, ForeignKey('users.id'))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    teams = relationship("Team", back_populates="workspace")
    projects = relationship("Project", back_populates="workspace")
    
    def __repr__(self):
        return f"<Workspace {self.name}>"

class Project(Base):
    __tablename__ = 'projects'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text)
    workspace_id = Column(String, ForeignKey('workspaces.id'))
    repository_url = Column(String)
    created_by = Column(String, ForeignKey('users.id'))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    status = Column(String, default="active")
    
    # Relationships
    workspace = relationship("Workspace", back_populates="projects")
    users = relationship("User", secondary=lambda: project_user_association)
    tasks = relationship("Task", back_populates="project")
    
    def __repr__(self):
        return f"<Project {self.name}>"

class Task(Base):
    __tablename__ = 'tasks'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    assigned_to = Column(String, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_by = Column(String, ForeignKey('users.id'))
    project_id = Column(String, ForeignKey('projects.id'))
    team_id = Column(String, ForeignKey('teams.id'))
    status = Column(Enum(TaskStatus), default=TaskStatus.CREATED, nullable=False)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False)
    type = Column(String, nullable=False)
    requires_validation = Column(Boolean, default=False)
    success_criteria = Column(JSON, default={})
    max_iterations = Column(Integer, default=5)
    iterations = Column(Integer, default=0)
    progress = Column(Integer, default=0)  # 0-100%
    due_date = Column(DateTime)
    time_estimate = Column(Float)  # In hours
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    assignee = relationship("User", foreign_keys=[assigned_to], back_populates="tasks")
    project = relationship("Project", back_populates="tasks")
    team = relationship("Team", back_populates="tasks")
    comments = relationship("TaskComment", back_populates="task", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary=lambda: task_tag_association)
    
    def __repr__(self):
        return f"<Task {self.title} ({self.status})>"

class TaskComment(Base):
    __tablename__ = 'task_comments'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey('tasks.id'), nullable=False)
    author_id = Column(String, ForeignKey('users.id'), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    task = relationship("Task", back_populates="comments")
    author = relationship("User", back_populates="comments")
    
    def __repr__(self):
        return f"<TaskComment by {self.author_id} on {self.task_id}>"

class Tag(Base):
    __tablename__ = 'tags'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True)
    color = Column(String, default="#4285f4")
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    tasks = relationship("Task", secondary=lambda: task_tag_association)
    
    def __repr__(self):
        return f"<Tag {self.name}>"

class Budget(Base):
    __tablename__ = 'budgets'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    team_id = Column(String, ForeignKey('teams.id'), nullable=False)
    total_budget = Column(Float, nullable=False)
    remaining_budget = Column(Float, nullable=False)
    start_date = Column(DateTime, nullable=False, default=func.now())
    end_date = Column(DateTime)
    alert_threshold = Column(Float, default=0.8)
    tier_constraints = Column(JSON, default={})
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    team = relationship("Team")
    alerts = relationship("SpendingAlert", back_populates="budget")
    
    def __repr__(self):
        return f"<Budget for team {self.team_id}>"

class SpendingAlert(Base):
    __tablename__ = 'spending_alerts'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    team_id = Column(String, ForeignKey('teams.id'), nullable=False)
    budget_id = Column(String, ForeignKey('budgets.id'), nullable=False)
    alert_type = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    current_spending = Column(Float, nullable=False)
    budget_limit = Column(Float, nullable=False)
    percentage_used = Column(Float, nullable=False)
    topic_name = Column(String)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    budget = relationship("Budget", back_populates="alerts")
    team = relationship("Team")
    
    def __repr__(self):
        return f"<SpendingAlert for team {self.team_id} ({self.alert_type})>"

class TopicBudget(Base):
    __tablename__ = 'topic_budgets'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    team_id = Column(String, ForeignKey('teams.id'), nullable=False)
    topic_name = Column(String, nullable=False)
    total_budget = Column(Float, nullable=False)
    remaining_budget = Column(Float, nullable=False)
    start_date = Column(DateTime, nullable=False, default=func.now())
    end_date = Column(DateTime)
    alert_threshold = Column(Float, default=0.8)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    team = relationship("Team")
    
    def __repr__(self):
        return f"<TopicBudget for {self.topic_name} in team {self.team_id}>" 