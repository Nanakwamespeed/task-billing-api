from datetime import datetime, timezone
from enum import Enum as PyEnum
from app.extensions import db


def utc_now():
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


class TaskStatus(PyEnum):
    """Enumeration for task status values."""
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'


class TaskPriority(PyEnum):
    """Enumeration for task priority values."""
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'


class Task(db.Model):
    """Task model for project/task management."""
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(
        db.Enum(TaskStatus),
        default=TaskStatus.PENDING,
        nullable=False
    )
    priority = db.Column(
        db.Enum(TaskPriority),
        default=TaskPriority.MEDIUM,
        nullable=False
    )
    due_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    def to_dict(self):
        """Serialize task to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'status': self.status.value if self.status else None,
            'priority': self.priority.value if self.priority else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<Task {self.title}>'
