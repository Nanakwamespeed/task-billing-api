import os
from datetime import timedelta


class Config:
    """Base configuration class."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///taskbill.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY', '')
    PAYSTACK_PUBLIC_KEY = os.environ.get('PAYSTACK_PUBLIC_KEY', '')

    SWAGGER = {
        'title': 'Task & Billing Manager API',
        'uiversion': 3,
        'version': '1.0.0',
        'description': 'A professional REST API for task management and payment processing via Paystack',
        'termsOfService': '',
        'specs_route': '/api/docs/',
        'headers': [],
        'specs': [
            {
                'endpoint': 'apispec',
                'route': '/api/docs/apispec.json',
            }
        ],
        'securityDefinitions': {
            'Bearer': {
                'type': 'apiKey',
                'name': 'Authorization',
                'in': 'header',
                'description': 'JWT Authorization header using the Bearer scheme. Example: "Bearer {token}"'
            }
        },
        'security': [
            {'Bearer': []}
        ]
    }


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_SECRET_KEY = 'test-jwt-secret'
    PAYSTACK_SECRET_KEY = 'sk_test_fake_key_for_testing'


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False

    @classmethod
    def init_app(cls, app):
        """Initialize production-specific settings."""
        database_url = os.environ.get('DATABASE_URL', '')
        if database_url.startswith('postgres://'):
            os.environ['DATABASE_URL'] = database_url.replace('postgres://', 'postgresql://', 1)
            app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
