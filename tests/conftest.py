import pytest
from flask_jwt_extended import create_access_token
from app import create_app
from app.extensions import db
from app.models import User, Task, Payment
from app.models.task import TaskStatus, TaskPriority
from app.models.payment import PaymentStatus


@pytest.fixture
def app():
    """Create and configure a test application instance."""
    app = create_app('testing')

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client for the application."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test CLI runner for the application."""
    return app.test_cli_runner()


@pytest.fixture
def test_user(app):
    """Create a test user in the database."""
    with app.app_context():
        user = User(
            email='testuser@example.com',
            full_name='Test User'
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        user_data = {
            'id': user.id,
            'email': user.email,
            'full_name': user.full_name
        }
        return user_data


@pytest.fixture
def auth_headers(app, test_user):
    """Create authentication headers with a valid JWT token."""
    with app.app_context():
        access_token = create_access_token(identity=str(test_user['id']))
        return {'Authorization': f'Bearer {access_token}'}


@pytest.fixture
def test_task(app, test_user):
    """Create a test task in the database."""
    with app.app_context():
        task = Task(
            user_id=test_user['id'],
            title='Test Task',
            description='This is a test task',
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM
        )
        db.session.add(task)
        db.session.commit()

        task_data = {
            'id': task.id,
            'user_id': task.user_id,
            'title': task.title
        }
        return task_data


@pytest.fixture
def test_payment(app, test_user):
    """Create a test payment in the database."""
    with app.app_context():
        payment = Payment(
            user_id=test_user['id'],
            reference='TASKBILL-TEST123456',
            amount=10000,
            currency='GHS',
            status=PaymentStatus.PENDING,
            description='Test payment'
        )
        db.session.add(payment)
        db.session.commit()

        payment_data = {
            'id': payment.id,
            'user_id': payment.user_id,
            'reference': payment.reference
        }
        return payment_data


@pytest.fixture
def other_user(app):
    """Create another test user for permission tests."""
    with app.app_context():
        user = User(
            email='otheruser@example.com',
            full_name='Other User'
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        user_data = {
            'id': user.id,
            'email': user.email,
            'full_name': user.full_name
        }
        return user_data


@pytest.fixture
def other_user_task(app, other_user):
    """Create a task owned by another user."""
    with app.app_context():
        task = Task(
            user_id=other_user['id'],
            title='Other User Task',
            description='This task belongs to another user',
            status=TaskStatus.PENDING,
            priority=TaskPriority.LOW
        )
        db.session.add(task)
        db.session.commit()

        task_data = {
            'id': task.id,
            'user_id': task.user_id,
            'title': task.title
        }
        return task_data
