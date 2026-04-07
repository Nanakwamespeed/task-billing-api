from flask import Blueprint

# Create blueprints
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
tasks_bp = Blueprint('tasks', __name__, url_prefix='/api/tasks')
payments_bp = Blueprint('payments', __name__, url_prefix='/api/payments')

# Import routes to register them with blueprints
from app.routes import auth, tasks, payments

__all__ = ['auth_bp', 'tasks_bp', 'payments_bp']
