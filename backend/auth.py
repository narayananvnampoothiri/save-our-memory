import re
import time
import secrets
import hashlib
import hmac
from functools import wraps
from datetime import datetime, timedelta
from flask import request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from backend.config import Config
from backend.database import get_db

# Serializer for stateless authentication tokens
serializer = URLSafeTimedSerializer(Config.SECRET_KEY, salt='som-auth-token-salt')

# Rate limiting dictionary in memory: {key: [timestamp, timestamp, ...]}
_rate_limits = {}

def check_rate_limit(key: str, max_requests: int = 5, window_seconds: int = 60) -> bool:
    """Returns True if within limit, False if rate exceeded."""
    now = time.time()
    timestamps = _rate_limits.get(key, [])
    # Filter out timestamps outside window
    timestamps = [t for t in timestamps if now - t < window_seconds]
    if len(timestamps) >= max_requests:
        _rate_limits[key] = timestamps
        return False
    timestamps.append(now)
    _rate_limits[key] = timestamps
    return True

def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validates strong password rules."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r'[0-9!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one number or special character."
    return True, ""

def validate_username(username: str) -> tuple[bool, str]:
    """Validates username format."""
    username = username.strip()
    if len(username) < 3 or len(username) > 30:
        return False, "Username must be between 3 and 30 characters."
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscores."
    return True, ""

def validate_email(email: str) -> bool:
    """Validates email format."""
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return bool(re.match(pattern, email.strip()))

def generate_auth_token(user_id: int) -> str:
    """Generates a secure, signed URL-safe authentication token."""
    return serializer.dumps({'user_id': user_id, 'created_at': time.time()})

def decode_auth_token(token: str) -> int | None:
    """Decodes and validates a signed auth token. Returns user_id or None."""
    try:
        max_age = Config.TOKEN_EXPIRE_HOURS * 3600
        data = serializer.loads(token, max_age=max_age)
        return data.get('user_id')
    except (SignatureExpired, BadSignature, Exception):
        return None

def hash_reset_code(code: str) -> str:
    """Hashes a verification OTP code with SHA-256 for secure DB storage."""
    return hashlib.sha256(f"{code}:{Config.SECRET_KEY}".encode('utf-8')).hexdigest()

def verify_reset_code_hash(code: str, stored_hash: str) -> bool:
    """Safely compares verification code hash in constant time."""
    candidate_hash = hash_reset_code(code)
    return hmac.compare_digest(candidate_hash, stored_hash)

def require_auth(f):
    """Decorator to require a valid session/bearer token for an endpoint."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        token = None
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1].strip()
        elif 'token' in request.args:
            # Query param support for media/streaming requests
            token = request.args.get('token', '').strip()
        elif 'som_token' in request.cookies:
            token = request.cookies.get('som_token', '').strip()

        if not token:
            return jsonify({'error': 'Authentication required. Please log in.'}), 401

        user_id = decode_auth_token(token)
        if not user_id:
            return jsonify({'error': 'Session expired or invalid. Please log in again.'}), 401

        db = get_db()
        user = db.execute(
            "SELECT id, name, username, email, profile_picture, bio, created_at FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()

        if not user:
            return jsonify({'error': 'User account not found.'}), 401

        g.current_user = dict(user)
        return f(*args, **kwargs)
    return decorated
