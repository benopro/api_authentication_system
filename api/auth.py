from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, verify_jwt_in_request
from datetime import timedelta
from functools import wraps
from flask import jsonify, request
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

jwt = JWTManager()

def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            # Get token from header
            auth_header = request.headers.get('Authorization')
            logger.debug(f"Auth header: {auth_header}")
            
            if not auth_header:
                return jsonify({'error': 'No Authorization header'}), 401
                
            # Check Bearer format
            parts = auth_header.split()
            if parts[0].lower() != 'bearer':
                return jsonify({'error': 'Authorization header must start with Bearer'}), 401
            elif len(parts) == 1:
                return jsonify({'error': 'Token missing'}), 401
            elif len(parts) > 2:
                return jsonify({'error': 'Authorization header must be Bearer token'}), 401
                
            token = parts[1]
            logger.debug(f"Extracted token: {token}")
            
            # Verify token
            verify_jwt_in_request()
            current_user = get_jwt_identity()
            logger.debug(f"Current user: {current_user}")
            
            if not current_user:
                return jsonify({'error': 'Invalid user in token'}), 401
                
            request.user_id = current_user
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            return jsonify({
                'error': 'Invalid token',
                'details': str(e)
            }), 401
            
    return decorated

def generate_token(user_id: int) -> str:
    # Convert user_id to string before creating token
    return create_access_token(
        identity=str(user_id),
        expires_delta=timedelta(days=1)
    )