from datetime import datetime, timezone
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import Task
from app.models.task import TaskStatus, TaskPriority
from app.routes import tasks_bp
from app.utils import paginate_query, success_response, error_response


@tasks_bp.route('', methods=['GET'])
@jwt_required()
def get_tasks():
    """
    Get all tasks for the authenticated user
    ---
    tags:
      - Tasks
    security:
      - Bearer: []
    parameters:
      - in: query
        name: status
        type: string
        enum: [pending, in_progress, completed, cancelled]
        description: Filter by task status
      - in: query
        name: priority
        type: string
        enum: [low, medium, high]
        description: Filter by task priority
      - in: query
        name: page
        type: integer
        default: 1
        description: Page number
      - in: query
        name: per_page
        type: integer
        default: 10
        description: Items per page (max 100)
    responses:
      200:
        description: Tasks retrieved successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: Tasks retrieved successfully
            data:
              type: array
              items:
                type: object
            meta:
              type: object
              properties:
                page:
                  type: integer
                per_page:
                  type: integer
                total:
                  type: integer
      401:
        description: Unauthorized
    """
    current_user_id = get_jwt_identity()

    query = Task.query.filter_by(user_id=int(current_user_id))

    status = request.args.get('status')
    if status:
        try:
            status_enum = TaskStatus(status)
            query = query.filter_by(status=status_enum)
        except ValueError:
            return error_response(f'Invalid status: {status}', status_code=400)

    priority = request.args.get('priority')
    if priority:
        try:
            priority_enum = TaskPriority(priority)
            query = query.filter_by(priority=priority_enum)
        except ValueError:
            return error_response(f'Invalid priority: {priority}', status_code=400)

    query = query.order_by(Task.created_at.desc())

    page = request.args.get('page', 1)
    per_page = request.args.get('per_page', 10)

    tasks, meta = paginate_query(query, page, per_page)

    return success_response(
        'Tasks retrieved successfully',
        data=tasks,
        meta=meta
    )


@tasks_bp.route('', methods=['POST'])
@jwt_required()
def create_task():
    """
    Create a new task
    ---
    tags:
      - Tasks
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - title
          properties:
            title:
              type: string
              example: Complete API documentation
            description:
              type: string
              example: Write comprehensive docs for all endpoints
            priority:
              type: string
              enum: [low, medium, high]
              example: high
            due_date:
              type: string
              format: date-time
              example: "2025-12-31T23:59:59"
    responses:
      201:
        description: Task created successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: Task created successfully
            data:
              type: object
      400:
        description: Validation error
      401:
        description: Unauthorized
    """
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return error_response('Request body is required', status_code=400)

    title = data.get('title', '').strip()
    if not title:
        return error_response('Title is required', errors={'title': 'Title is required'}, status_code=400)

    description = data.get('description', '').strip() or None
    priority_str = data.get('priority', 'medium')
    due_date_str = data.get('due_date')

    try:
        priority = TaskPriority(priority_str)
    except ValueError:
        return error_response(
            f'Invalid priority: {priority_str}',
            errors={'priority': 'Must be one of: low, medium, high'},
            status_code=400
        )

    due_date = None
    if due_date_str:
        try:
            due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
        except ValueError:
            return error_response(
                'Invalid due_date format',
                errors={'due_date': 'Must be ISO 8601 format (e.g., 2025-12-31T23:59:59)'},
                status_code=400
            )

    task = Task(
        user_id=int(current_user_id),
        title=title,
        description=description,
        priority=priority,
        due_date=due_date,
        status=TaskStatus.PENDING
    )

    db.session.add(task)
    db.session.commit()

    return success_response(
        'Task created successfully',
        data=task.to_dict(),
        status_code=201
    )


@tasks_bp.route('/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    """
    Get a single task by ID
    ---
    tags:
      - Tasks
    security:
      - Bearer: []
    parameters:
      - in: path
        name: task_id
        type: integer
        required: true
        description: Task ID
    responses:
      200:
        description: Task retrieved successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: Task retrieved successfully
            data:
              type: object
      404:
        description: Task not found
      401:
        description: Unauthorized
    """
    current_user_id = get_jwt_identity()

    task = Task.query.filter_by(id=task_id, user_id=int(current_user_id)).first()

    if not task:
        return error_response('Task not found', status_code=404)

    return success_response(
        'Task retrieved successfully',
        data=task.to_dict()
    )


@tasks_bp.route('/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    """
    Update a task
    ---
    tags:
      - Tasks
    security:
      - Bearer: []
    parameters:
      - in: path
        name: task_id
        type: integer
        required: true
        description: Task ID
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            title:
              type: string
              example: Updated task title
            description:
              type: string
              example: Updated description
            status:
              type: string
              enum: [pending, in_progress, completed, cancelled]
              example: in_progress
            priority:
              type: string
              enum: [low, medium, high]
              example: high
            due_date:
              type: string
              format: date-time
              example: "2025-12-31T23:59:59"
    responses:
      200:
        description: Task updated successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: Task updated successfully
            data:
              type: object
      400:
        description: Validation error
      404:
        description: Task not found
      401:
        description: Unauthorized
    """
    current_user_id = get_jwt_identity()

    task = Task.query.filter_by(id=task_id, user_id=int(current_user_id)).first()

    if not task:
        return error_response('Task not found', status_code=404)

    data = request.get_json()

    if not data:
        return error_response('Request body is required', status_code=400)

    if 'title' in data:
        title = data['title'].strip()
        if not title:
            return error_response('Title cannot be empty', errors={'title': 'Title is required'}, status_code=400)
        task.title = title

    if 'description' in data:
        task.description = data['description'].strip() or None

    if 'status' in data:
        try:
            task.status = TaskStatus(data['status'])
        except ValueError:
            return error_response(
                f"Invalid status: {data['status']}",
                errors={'status': 'Must be one of: pending, in_progress, completed, cancelled'},
                status_code=400
            )

    if 'priority' in data:
        try:
            task.priority = TaskPriority(data['priority'])
        except ValueError:
            return error_response(
                f"Invalid priority: {data['priority']}",
                errors={'priority': 'Must be one of: low, medium, high'},
                status_code=400
            )

    if 'due_date' in data:
        if data['due_date'] is None:
            task.due_date = None
        else:
            try:
                task.due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
            except ValueError:
                return error_response(
                    'Invalid due_date format',
                    errors={'due_date': 'Must be ISO 8601 format'},
                    status_code=400
                )

    db.session.commit()

    return success_response(
        'Task updated successfully',
        data=task.to_dict()
    )


@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    """
    Cancel a task (soft delete)
    ---
    tags:
      - Tasks
    security:
      - Bearer: []
    parameters:
      - in: path
        name: task_id
        type: integer
        required: true
        description: Task ID
    responses:
      200:
        description: Task cancelled successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: Task cancelled
      404:
        description: Task not found
      401:
        description: Unauthorized
    """
    current_user_id = get_jwt_identity()

    task = Task.query.filter_by(id=task_id, user_id=int(current_user_id)).first()

    if not task:
        return error_response('Task not found', status_code=404)

    task.status = TaskStatus.CANCELLED
    db.session.commit()

    return success_response('Task cancelled')


@tasks_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_task_stats():
    """
    Get task statistics for the authenticated user
    ---
    tags:
      - Tasks
    security:
      - Bearer: []
    responses:
      200:
        description: Task statistics retrieved successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: Task statistics retrieved successfully
            data:
              type: object
              properties:
                total:
                  type: integer
                  example: 15
                pending:
                  type: integer
                  example: 5
                in_progress:
                  type: integer
                  example: 3
                completed:
                  type: integer
                  example: 6
                cancelled:
                  type: integer
                  example: 1
                overdue:
                  type: integer
                  example: 2
      401:
        description: Unauthorized
    """
    current_user_id = get_jwt_identity()

    base_query = Task.query.filter_by(user_id=int(current_user_id))

    total = base_query.count()
    pending = base_query.filter_by(status=TaskStatus.PENDING).count()
    in_progress = base_query.filter_by(status=TaskStatus.IN_PROGRESS).count()
    completed = base_query.filter_by(status=TaskStatus.COMPLETED).count()
    cancelled = base_query.filter_by(status=TaskStatus.CANCELLED).count()

    overdue = base_query.filter(
        Task.due_date < datetime.now(timezone.utc),
        Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
    ).count()

    stats = {
        'total': total,
        'pending': pending,
        'in_progress': in_progress,
        'completed': completed,
        'cancelled': cancelled,
        'overdue': overdue
    }

    return success_response(
        'Task statistics retrieved successfully',
        data=stats
    )
