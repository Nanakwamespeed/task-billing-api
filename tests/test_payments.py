import json
import hashlib
import hmac
import pytest
from unittest.mock import patch, MagicMock


class TestPaymentInitialize:
    """Tests for payment initialization endpoint."""

    @patch('app.services.paystack.requests.post')
    def test_initialize_payment(self, mock_post, client, auth_headers):
        """Test successful payment initialization."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': True,
            'data': {
                'authorization_url': 'https://checkout.paystack.com/test',
                'access_code': 'test_access_code',
                'reference': 'TASKBILL-TEST123456'
            }
        }
        mock_post.return_value = mock_response

        response = client.post(
            '/api/payments/initialize',
            headers=auth_headers,
            json={
                'amount': 100.50,
                'description': 'Test payment'
            }
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'authorization_url' in data['data']
        assert 'reference' in data['data']
        assert 'payment_id' in data['data']

    def test_initialize_payment_missing_amount(self, client, auth_headers):
        """Test payment initialization without amount."""
        response = client.post(
            '/api/payments/initialize',
            headers=auth_headers,
            json={'description': 'Test payment'}
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'amount' in data.get('errors', {})

    def test_initialize_payment_invalid_amount(self, client, auth_headers):
        """Test payment initialization with invalid amount."""
        response = client.post(
            '/api/payments/initialize',
            headers=auth_headers,
            json={'amount': -100}
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False

    def test_initialize_payment_unauthenticated(self, client):
        """Test payment initialization without authentication."""
        response = client.post(
            '/api/payments/initialize',
            json={'amount': 100}
        )

        assert response.status_code == 401

    @patch('app.services.paystack.requests.post')
    def test_initialize_payment_paystack_error(self, mock_post, client, auth_headers):
        """Test payment initialization when Paystack returns error."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            'status': False,
            'message': 'Invalid API key'
        }
        mock_post.return_value = mock_response

        response = client.post(
            '/api/payments/initialize',
            headers=auth_headers,
            json={'amount': 100}
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False


class TestPaymentVerify:
    """Tests for payment verification endpoint."""

    @patch('app.services.paystack.requests.get')
    def test_verify_payment(self, mock_get, client, auth_headers, test_payment):
        """Test successful payment verification."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': True,
            'data': {
                'status': 'success',
                'amount': 10000,
                'currency': 'GHS',
                'reference': test_payment['reference'],
                'id': 123456789,
                'customer': {'email': 'test@example.com'}
            }
        }
        mock_get.return_value = mock_response

        response = client.get(
            f'/api/payments/verify/{test_payment["reference"]}',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['status'] == 'success'

    def test_verify_nonexistent_payment(self, client, auth_headers):
        """Test verification of non-existent payment."""
        response = client.get(
            '/api/payments/verify/NONEXISTENT-REF',
            headers=auth_headers
        )

        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False


class TestPaymentWebhook:
    """Tests for Paystack webhook endpoint."""

    def test_webhook_valid_signature(self, app, client, test_payment):
        """Test webhook with valid signature."""
        payload = json.dumps({
            'event': 'charge.success',
            'data': {
                'reference': test_payment['reference'],
                'id': 123456789
            }
        })

        with app.app_context():
            secret_key = app.config['PAYSTACK_SECRET_KEY']

        signature = hmac.new(
            secret_key.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()

        response = client.post(
            '/api/payments/webhook',
            data=payload,
            content_type='application/json',
            headers={'X-Paystack-Signature': signature}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    def test_webhook_invalid_signature(self, client, test_payment):
        """Test webhook with invalid signature."""
        payload = json.dumps({
            'event': 'charge.success',
            'data': {
                'reference': test_payment['reference'],
                'id': 123456789
            }
        })

        response = client.post(
            '/api/payments/webhook',
            data=payload,
            content_type='application/json',
            headers={'X-Paystack-Signature': 'invalid_signature'}
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False

    def test_webhook_missing_signature(self, client):
        """Test webhook without signature header."""
        response = client.post(
            '/api/payments/webhook',
            json={
                'event': 'charge.success',
                'data': {'reference': 'TEST-REF'}
            }
        )

        assert response.status_code == 400


class TestPaymentList:
    """Tests for payment listing endpoint."""

    def test_get_payments(self, client, auth_headers, test_payment):
        """Test getting user payments."""
        response = client.get(
            '/api/payments',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert isinstance(data['data'], list)
        assert 'meta' in data

    def test_get_payments_filter_status(self, client, auth_headers, test_payment):
        """Test filtering payments by status."""
        response = client.get(
            '/api/payments?status=pending',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        for payment in data['data']:
            assert payment['status'] == 'pending'

    def test_get_single_payment(self, client, auth_headers, test_payment):
        """Test getting a single payment by ID."""
        response = client.get(
            f'/api/payments/{test_payment["id"]}',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['reference'] == test_payment['reference']

    def test_get_nonexistent_payment(self, client, auth_headers):
        """Test getting a non-existent payment."""
        response = client.get(
            '/api/payments/99999',
            headers=auth_headers
        )

        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
