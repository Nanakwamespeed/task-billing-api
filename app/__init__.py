import os
from flask import Flask, jsonify
from flask_jwt_extended.exceptions import (
    NoAuthorizationError,
    InvalidHeaderError,
    WrongTokenError,
    RevokedTokenError,
    FreshTokenRequired
)
from jwt.exceptions import ExpiredSignatureError, DecodeError

from app.config import config
from app.extensions import db, migrate, jwt, swagger


def create_app(config_name=None):
    """Application factory for creating the Flask app instance."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    if hasattr(config[config_name], 'init_app'):
        config[config_name].init_app(app)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    swagger.init_app(app)

    from app.routes import auth_bp, tasks_bp, payments_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(payments_bp)

    register_error_handlers(app)

    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint for monitoring."""
        return jsonify({
            'success': True,
            'message': 'Task & Billing API is running',
            'data': {
                'status': 'healthy',
                'version': '1.0.0'
            }
        })

    return app


def register_error_handlers(app):
    """Register global error handlers for the application."""

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'message': 'Bad request',
            'errors': str(error.description) if hasattr(error, 'description') else None
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'message': 'Resource not found'
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'success': False,
            'message': 'Method not allowed'
        }), 405

    @app.errorhandler(422)
    def unprocessable_entity(error):
        return jsonify({
            'success': False,
            'message': 'Unprocessable entity',
            'errors': str(error.description) if hasattr(error, 'description') else None
        }), 422

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

    @app.errorhandler(NoAuthorizationError)
    def handle_no_authorization(error):
        return jsonify({
            'success': False,
            'message': 'Authorization header is missing'
        }), 401

    @app.errorhandler(InvalidHeaderError)
    def handle_invalid_header(error):
        return jsonify({
            'success': False,
            'message': 'Invalid authorization header format'
        }), 401

    @app.errorhandler(WrongTokenError)
    def handle_wrong_token(error):
        return jsonify({
            'success': False,
            'message': 'Wrong token type provided'
        }), 401

    @app.errorhandler(RevokedTokenError)
    def handle_revoked_token(error):
        return jsonify({
            'success': False,
            'message': 'Token has been revoked'
        }), 401

    @app.errorhandler(FreshTokenRequired)
    def handle_fresh_token_required(error):
        return jsonify({
            'success': False,
            'message': 'Fresh token required'
        }), 401

    @app.errorhandler(ExpiredSignatureError)
    def handle_expired_signature(error):
        return jsonify({
            'success': False,
            'message': 'Token has expired'
        }), 401

    @app.errorhandler(DecodeError)
    def handle_decode_error(error):
        return jsonify({
            'success': False,
            'message': 'Invalid token'
        }), 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'success': False,
            'message': 'Token has expired'
        }), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            'success': False,
            'message': 'Invalid token'
        }), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            'success': False,
            'message': 'Authorization token is required'
        }), 401

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'success': False,
            'message': 'Token has been revoked'
        }), 401
