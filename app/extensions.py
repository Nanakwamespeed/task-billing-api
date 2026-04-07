from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flasgger import Swagger

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
swagger = Swagger()

# Token blacklist for logout functionality
token_blacklist = set()


@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(jwt_header, jwt_payload):
    """Check if a token has been blacklisted (logged out)."""
    jti = jwt_payload['jti']
    return jti in token_blacklist
