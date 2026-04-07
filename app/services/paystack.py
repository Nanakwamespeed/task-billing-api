import hashlib
import hmac
import requests
from flask import current_app


class PaystackService:
    """Service class for Paystack API integration."""

    BASE_URL = "https://api.paystack.co"

    def __init__(self):
        """Initialize PaystackService with API credentials from config."""
        self.secret_key = current_app.config.get('PAYSTACK_SECRET_KEY', '')
        self.headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }

    def initialize_transaction(self, email, amount_ghs, reference, description=None):
        """
        Initialize a Paystack transaction.

        Args:
            email: Customer's email address
            amount_ghs: Amount in GHS (cedis)
            reference: Unique transaction reference
            description: Optional transaction description

        Returns:
            dict: Contains authorization_url, access_code, reference on success
                  Contains error message on failure
        """
        # Convert cedis to pesewas (multiply by 100)
        amount_pesewas = int(float(amount_ghs) * 100)

        payload = {
            "email": email,
            "amount": amount_pesewas,
            "reference": reference,
            "currency": "GHS"
        }

        if description:
            payload["metadata"] = {"description": description}

        try:
            response = requests.post(
                f"{self.BASE_URL}/transaction/initialize",
                json=payload,
                headers=self.headers,
                timeout=30
            )

            data = response.json()

            if response.status_code == 200 and data.get('status'):
                return {
                    'success': True,
                    'authorization_url': data['data']['authorization_url'],
                    'access_code': data['data']['access_code'],
                    'reference': data['data']['reference']
                }
            else:
                return {
                    'success': False,
                    'message': data.get('message', 'Failed to initialize transaction')
                }

        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'message': f'Network error: {str(e)}'
            }

    def verify_transaction(self, reference):
        """
        Verify a Paystack transaction by reference.

        Args:
            reference: Transaction reference to verify

        Returns:
            dict: Contains status, amount, customer info on success
                  Contains error message on failure
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/transaction/verify/{reference}",
                headers=self.headers,
                timeout=30
            )

            data = response.json()

            if response.status_code == 200 and data.get('status'):
                transaction_data = data['data']
                return {
                    'success': True,
                    'status': transaction_data['status'],
                    'amount': transaction_data['amount'],
                    'currency': transaction_data['currency'],
                    'reference': transaction_data['reference'],
                    'paystack_id': str(transaction_data['id']),
                    'customer': transaction_data.get('customer', {}),
                    'paid_at': transaction_data.get('paid_at'),
                    'channel': transaction_data.get('channel')
                }
            else:
                return {
                    'success': False,
                    'message': data.get('message', 'Failed to verify transaction')
                }

        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'message': f'Network error: {str(e)}'
            }

    def verify_webhook_signature(self, payload, signature):
        """
        Verify Paystack webhook signature using HMAC SHA512.

        Args:
            payload: Raw request body as bytes
            signature: X-Paystack-Signature header value

        Returns:
            bool: True if signature is valid, False otherwise
        """
        if not signature or not self.secret_key:
            return False

        expected_signature = hmac.new(
            self.secret_key.encode('utf-8'),
            payload if isinstance(payload, bytes) else payload.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()

        return hmac.compare_digest(expected_signature, signature)
