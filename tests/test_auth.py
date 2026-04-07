import json
import pytest


class TestAuthRegister:
    """Tests for user registration endpoint."""

    def test_register_success(self, client):
        """Test successful user registration."""
        response = client.post(
            '/api/auth/register',
            json={
                'email': 'newuser@example.com',
                'password': 'securepass123',
                'full_name': 'New User'
            }
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['message'] == 'User registered successfully'
        assert 'access_token' in data['data']
        assert 'refresh_token' in data['data']
        assert data['data']['user']['email'] == 'newuser@example.com'
        assert data['data']['user']['full_name'] == 'New User'

    def test_register_duplicate_email(self, client, test_user):
        """Test registration with an already registered email."""
        response = client.post(
            '/api/auth/register',
            json={
                'email': test_user['email'],
                'password': 'securepass123',
                'full_name': 'Another User'
            }
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'already registered' in data['message'].lower()

    def test_register_invalid_email(self, client):
        """Test registration with invalid email format."""
        response = client.post(
            '/api/auth/register',
            json={
                'email': 'invalid-email',
                'password': 'securepass123',
                'full_name': 'Test User'
            }
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'email' in data.get('errors', {})

    def test_register_short_password(self, client):
        """Test registration with password shorter than 8 characters."""
        response = client.post(
            '/api/auth/register',
            json={
                'email': 'test@example.com',
                'password': 'short1',
                'full_name': 'Test User'
            }
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'password' in data.get('errors', {})

    def test_register_password_no_number(self, client):
        """Test registration with password containing no numbers."""
        response = client.post(
            '/api/auth/register',
            json={
                'email': 'test@example.com',
                'password': 'passwordonly',
                'full_name': 'Test User'
            }
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'password' in data.get('errors', {})

    def test_register_missing_fields(self, client):
        """Test registration with missing required fields."""
        response = client.post(
            '/api/auth/register',
            json={}
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False


class TestAuthLogin:
    """Tests for user login endpoint."""

    def test_login_success(self, client, test_user):
        """Test successful login."""
        response = client.post(
            '/api/auth/login',
            json={
                'email': test_user['email'],
                'password': 'password123'
            }
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['message'] == 'Login successful'
        assert 'access_token' in data['data']
        assert 'refresh_token' in data['data']
        assert data['data']['user']['email'] == test_user['email']

    def test_login_wrong_password(self, client, test_user):
        """Test login with incorrect password."""
        response = client.post(
            '/api/auth/login',
            json={
                'email': test_user['email'],
                'password': 'wrongpassword123'
            }
        )

        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'invalid' in data['message'].lower()

    def test_login_nonexistent_email(self, client):
        """Test login with non-existent email."""
        response = client.post(
            '/api/auth/login',
            json={
                'email': 'nonexistent@example.com',
                'password': 'password123'
            }
        )

        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['success'] is False

    def test_login_missing_fields(self, client):
        """Test login with missing fields."""
        response = client.post(
            '/api/auth/login',
            json={}
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False


class TestAuthProfile:
    """Tests for user profile endpoints."""

    def test_get_profile_authenticated(self, client, auth_headers, test_user):
        """Test getting profile with valid authentication."""
        response = client.get(
            '/api/auth/me',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['email'] == test_user['email']
        assert data['data']['full_name'] == test_user['full_name']

    def test_get_profile_unauthenticated(self, client):
        """Test getting profile without authentication."""
        response = client.get('/api/auth/me')

        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['success'] is False

    def test_update_profile(self, client, auth_headers):
        """Test updating user profile."""
        response = client.put(
            '/api/auth/me',
            headers=auth_headers,
            json={'full_name': 'Updated Name'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['full_name'] == 'Updated Name'


class TestAuthToken:
    """Tests for token management."""

    def test_refresh_token(self, app, client, test_user):
        """Test refreshing access token."""
        from flask_jwt_extended import create_refresh_token

        with app.app_context():
            refresh_token = create_refresh_token(identity=str(test_user['id']))

        response = client.post(
            '/api/auth/refresh',
            headers={'Authorization': f'Bearer {refresh_token}'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'access_token' in data['data']

    def test_logout(self, client, auth_headers):
        """Test logout functionality."""
        response = client.post(
            '/api/auth/logout',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'logged out' in data['message'].lower()
