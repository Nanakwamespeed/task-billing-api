import json
import pytest


class TestTaskCreate:
    """Tests for task creation endpoint."""

    def test_create_task(self, client, auth_headers):
        """Test successful task creation."""
        response = client.post(
            '/api/tasks',
            headers=auth_headers,
            json={
                'title': 'New Task',
                'description': 'Task description',
                'priority': 'high'
            }
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['title'] == 'New Task'
        assert data['data']['description'] == 'Task description'
        assert data['data']['priority'] == 'high'
        assert data['data']['status'] == 'pending'

    def test_create_task_minimal(self, client, auth_headers):
        """Test task creation with only required fields."""
        response = client.post(
            '/api/tasks',
            headers=auth_headers,
            json={'title': 'Minimal Task'}
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['title'] == 'Minimal Task'
        assert data['data']['priority'] == 'medium'

    def test_create_task_with_due_date(self, client, auth_headers):
        """Test task creation with due date."""
        response = client.post(
            '/api/tasks',
            headers=auth_headers,
            json={
                'title': 'Task with due date',
                'due_date': '2025-12-31T23:59:59'
            }
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['due_date'] is not None

    def test_create_task_missing_title(self, client, auth_headers):
        """Test task creation without title."""
        response = client.post(
            '/api/tasks',
            headers=auth_headers,
            json={'description': 'Description only'}
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'title' in data.get('errors', {})

    def test_create_task_unauthenticated(self, client):
        """Test task creation without authentication."""
        response = client.post(
            '/api/tasks',
            json={'title': 'Unauthorized Task'}
        )

        assert response.status_code == 401


class TestTaskList:
    """Tests for task listing endpoint."""

    def test_get_tasks_paginated(self, client, auth_headers, test_task):
        """Test getting paginated tasks."""
        response = client.get(
            '/api/tasks?page=1&per_page=10',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert isinstance(data['data'], list)
        assert 'meta' in data
        assert data['meta']['page'] == 1
        assert data['meta']['per_page'] == 10

    def test_get_tasks_filter_by_status(self, client, auth_headers, test_task):
        """Test filtering tasks by status."""
        response = client.get(
            '/api/tasks?status=pending',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        for task in data['data']:
            assert task['status'] == 'pending'

    def test_get_tasks_filter_by_priority(self, client, auth_headers, test_task):
        """Test filtering tasks by priority."""
        response = client.get(
            '/api/tasks?priority=medium',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        for task in data['data']:
            assert task['priority'] == 'medium'

    def test_get_tasks_invalid_status(self, client, auth_headers):
        """Test filtering with invalid status."""
        response = client.get(
            '/api/tasks?status=invalid',
            headers=auth_headers
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False


class TestTaskUpdate:
    """Tests for task update endpoint."""

    def test_update_task(self, client, auth_headers, test_task):
        """Test successful task update."""
        response = client.put(
            f'/api/tasks/{test_task["id"]}',
            headers=auth_headers,
            json={
                'title': 'Updated Title',
                'status': 'in_progress'
            }
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['title'] == 'Updated Title'
        assert data['data']['status'] == 'in_progress'

    def test_update_task_partial(self, client, auth_headers, test_task):
        """Test partial task update."""
        response = client.put(
            f'/api/tasks/{test_task["id"]}',
            headers=auth_headers,
            json={'priority': 'high'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['priority'] == 'high'
        assert data['data']['title'] == test_task['title']

    def test_update_nonexistent_task(self, client, auth_headers):
        """Test updating a non-existent task."""
        response = client.put(
            '/api/tasks/99999',
            headers=auth_headers,
            json={'title': 'Updated'}
        )

        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False


class TestTaskDelete:
    """Tests for task deletion endpoint."""

    def test_cancel_task(self, client, auth_headers, test_task):
        """Test cancelling a task (soft delete)."""
        response = client.delete(
            f'/api/tasks/{test_task["id"]}',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'cancelled' in data['message'].lower()

        get_response = client.get(
            f'/api/tasks/{test_task["id"]}',
            headers=auth_headers
        )
        get_data = json.loads(get_response.data)
        assert get_data['data']['status'] == 'cancelled'


class TestTaskStats:
    """Tests for task statistics endpoint."""

    def test_task_stats(self, client, auth_headers, test_task):
        """Test getting task statistics."""
        response = client.get(
            '/api/tasks/stats',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'total' in data['data']
        assert 'pending' in data['data']
        assert 'in_progress' in data['data']
        assert 'completed' in data['data']
        assert 'cancelled' in data['data']
        assert 'overdue' in data['data']


class TestTaskPermissions:
    """Tests for task permission checks."""

    def test_cannot_access_other_users_task(self, client, auth_headers, other_user_task):
        """Test that users cannot access tasks owned by other users."""
        response = client.get(
            f'/api/tasks/{other_user_task["id"]}',
            headers=auth_headers
        )

        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False

    def test_cannot_update_other_users_task(self, client, auth_headers, other_user_task):
        """Test that users cannot update tasks owned by other users."""
        response = client.put(
            f'/api/tasks/{other_user_task["id"]}',
            headers=auth_headers,
            json={'title': 'Hacked Title'}
        )

        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False

    def test_cannot_delete_other_users_task(self, client, auth_headers, other_user_task):
        """Test that users cannot delete tasks owned by other users."""
        response = client.delete(
            f'/api/tasks/{other_user_task["id"]}',
            headers=auth_headers
        )

        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
