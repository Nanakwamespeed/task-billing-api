from flask import request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from app.extensions import db, token_blacklist
from app.models import User
from app.models import User
from app.routes import auth_bp
from app.utils import validate_email, validate_password, success_response, error_response


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
            - full_name
          properties:
            email:
              type: string
              example: kwame@example.com
            password:
              type: string
              example: securepass123
            full_name:
              type: string
              example: Kwame Mensah
    responses:
      201:
        description: User registered successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: User registered successfully
            data:
              type: object
              properties:
                user:
                  type: object
                access_token:
                  type: string
                refresh_token:
                  type: string
      400:
        description: Validation error or email already exists
    """
    data = request.get_json()

    if not data:
        return error_response('Request body is required', status_code=400)

    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    full_name = data.get('full_name', '').strip()

    errors = {}

    if not email:
        errors['email'] = 'Email is required'
    elif not validate_email(email):
        errors['email'] = 'Invalid email format'

    if not full_name:
        errors['full_name'] = 'Full name is required'

    is_valid_password, password_error = validate_password(password)
    if not is_valid_password:
        errors['password'] = password_error

    if errors:
        return error_response('Validation failed', errors=errors, status_code=400)

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return error_response('Email already registered', errors={'email': 'This email is already in use'}, status_code=400)

    user = User(email=email, full_name=full_name)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return success_response(
        'User registered successfully',
        data={
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        },
        status_code=201
    )


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login with email and password
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
              example: kwame@example.com
            password:
              type: string
              example: securepass123
    responses:
      200:
        description: Login successful
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: Login successful
            data:
              type: object
              properties:
                user:
                  type: object
                access_token:
                  type: string
                refresh_token:
                  type: string
      401:
        description: Invalid credentials
    """
    data = request.get_json()

    if not data:
        return error_response('Request body is required', status_code=400)

    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return error_response('Email and password are required', status_code=400)

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return error_response('Invalid email or password', status_code=401)

    if not user.is_active:
        return error_response('Account is deactivated', status_code=401)

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return success_response(
        'Login successful',
        data={
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }
    )


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh access token using refresh token
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    responses:
      200:
        description: Token refreshed successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: Token refreshed successfully
            data:
              type: object
              properties:
                access_token:
                  type: string
      401:
        description: Invalid or expired refresh token
    """
    current_user_id = get_jwt_identity()
    access_token = create_access_token(identity=current_user_id)

    return success_response(
        'Token refreshed successfully',
        data={'access_token': access_token}
    )


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_profile():
    """
    Get current user profile
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    responses:
      200:
        description: User profile retrieved successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: Profile retrieved successfully
            data:
              type: object
      401:
        description: Unauthorized - invalid or missing token
    """
    current_user_id = get_jwt_identity()
    user = db.session.get(User, int(current_user_id))

    if not user:
        return error_response('User not found', status_code=404)

    return success_response(
        'Profile retrieved successfully',
        data=user.to_dict()
    )


@auth_bp.route('/me', methods=['PUT'])
@jwt_required()
def update_profile():
    """
    Update current user profile
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            full_name:
              type: string
              example: Kwame Asante Mensah
    responses:
      200:
        description: Profile updated successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: Profile updated successfully
            data:
              type: object
      400:
        description: Validation error
      401:
        description: Unauthorized
    """
    current_user_id = get_jwt_identity()
    user = db.session.get(User, int(current_user_id))

    if not user:
        return error_response('User not found', status_code=404)

    data = request.get_json()

    if not data:
        return error_response('Request body is required', status_code=400)

    full_name = data.get('full_name', '').strip()

    if full_name:
        if len(full_name) < 2:
            return error_response('Full name must be at least 2 characters', status_code=400)
        user.full_name = full_name

    db.session.commit()

    return success_response(
        'Profile updated successfully',
        data=user.to_dict()
    )


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Logout and blacklist the current token
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    responses:
      200:
        description: Logged out successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: Logged out successfully
      401:
        description: Unauthorized
    """
    jti = get_jwt()['jti']
    token_blacklist.add(jti)

    return success_response('Logged out successfully')
