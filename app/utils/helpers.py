import re
import uuid
from flask import jsonify


def validate_email(email):
    """
    Validate email format using regex.

    Args:
        email: Email string to validate

    Returns:
        bool: True if email format is valid, False otherwise
    """
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password(password):
    """
    Validate password strength.
    Requirements: minimum 8 characters, at least one number.

    Args:
        password: Password string to validate

    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if not password:
        return False, 'Password is required'

    if len(password) < 8:
        return False, 'Password must be at least 8 characters long'

    if not re.search(r'\d', password):
        return False, 'Password must contain at least one number'

    return True, None


def paginate_query(query, page=1, per_page=10):
    """
    Paginate a SQLAlchemy query and return items with metadata.

    Args:
        query: SQLAlchemy query object
        page: Page number (1-indexed)
        per_page: Number of items per page

    Returns:
        tuple: (items list, meta dict with pagination info)
    """
    page = max(1, int(page) if page else 1)
    per_page = min(100, max(1, int(per_page) if per_page else 10))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    items = [item.to_dict() for item in pagination.items]

    meta = {
        'page': page,
        'per_page': per_page,
        'total': pagination.total,
        'pages': pagination.pages,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    }

    return items, meta


def generate_reference():
    """
    Generate a unique payment reference for Paystack.

    Returns:
        str: Unique reference string in format TASKBILL-XXXXXXXXXXXX
    """
    return f"TASKBILL-{uuid.uuid4().hex[:12].upper()}"


def success_response(message, data=None, meta=None, status_code=200):
    """
    Create a standardized success response.

    Args:
        message: Human readable success message
        data: Response data (dict or list)
        meta: Pagination metadata (optional)
        status_code: HTTP status code

    Returns:
        tuple: (response dict, status code)
    """
    response = {
        'success': True,
        'message': message
    }

    if data is not None:
        response['data'] = data

    if meta is not None:
        response['meta'] = meta

    return jsonify(response), status_code


def error_response(message, errors=None, status_code=400):
    """
    Create a standardized error response.

    Args:
        message: Human readable error message
        errors: Dict of field-specific errors (optional)
        status_code: HTTP status code

    Returns:
        tuple: (response dict, status code)
    """
    response = {
        'success': False,
        'message': message
    }

    if errors is not None:
        response['errors'] = errors

    return jsonify(response), status_code
