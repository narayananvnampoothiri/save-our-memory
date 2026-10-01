import secrets
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash
from backend.config import Config
from backend.database import get_db
from backend.auth import (
    require_auth,
    generate_auth_token,
    validate_password_strength,
    validate_username,
    validate_email,
    hash_reset_code,
    verify_reset_code_hash,
    check_rate_limit
)
from backend.security import sanitize_user

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')

    if not name or not username or not email or not password:
        return jsonify({'error': 'Please fill in all required fields.'}), 400

    # Username validation
    valid_uname, uname_err = validate_username(username)
    if not valid_uname:
        return jsonify({'error': uname_err}), 400

    # Email validation
    if not validate_email(email):
        return jsonify({'error': 'Please provide a valid email address.'}), 400

    # Password confirmation
    if password != confirm_password:
        return jsonify({'error': 'Passwords do not match.'}), 400

    # Password strength
    valid_pwd, pwd_err = validate_password_strength(password)
    if not valid_pwd:
        return jsonify({'error': pwd_err}), 400

    db = get_db()
    # Check if username or email already taken
    existing = db.execute(
        "SELECT id, username, email FROM users WHERE username = ? OR email = ?",
        (username, email)
    ).fetchone()

    if existing:
        if existing['username'].lower() == username.lower():
            return jsonify({'error': 'This username is already taken. Please choose another.'}), 409
        if existing['email'].lower() == email.lower():
            return jsonify({'error': 'An account with this email already exists.'}), 409

    pwd_hash = generate_password_hash(password)

    cursor = db.execute(
        """
        INSERT INTO users (name, username, email, password_hash, created_at, updated_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        (name, username, email, pwd_hash)
    )
    db.commit()
    user_id = cursor.lastrowid

    token = generate_auth_token(user_id)
    user_row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    return jsonify({
        'message': 'Welcome to Save Our Memory! Your vault is ready ❤️',
        'token': token,
        'user': sanitize_user(dict(user_row), is_self=True)
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    ip = request.remote_addr or 'unknown'
    if not check_rate_limit(f"login_{ip}", max_requests=10, window_seconds=60):
        return jsonify({'error': 'Too many login attempts. Please wait a minute and try again.'}), 429

    data = request.get_json() or {}
    login_id = data.get('login', '').strip()
    password = data.get('password', '')

    if not login_id or not password:
        return jsonify({'error': 'Please provide your username/email and password.'}), 400

    db = get_db()
    user = db.execute(
        "SELECT * FROM users WHERE username = ? OR email = ?",
        (login_id, login_id.lower())
    ).fetchone()

    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'Invalid username or password.'}), 401

    token = generate_auth_token(user['id'])
    return jsonify({
        'message': f'Welcome back, {user["name"]} ❤️',
        'token': token,
        'user': sanitize_user(dict(user), is_self=True)
    }), 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    return jsonify({'message': 'Logged out successfully.'}), 200

@auth_bp.route('/me', methods=['GET'])
@require_auth
def get_me():
    return jsonify({'user': sanitize_user(g.current_user, is_self=True)}), 200

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    ip = request.remote_addr or 'unknown'
    if not check_rate_limit(f"forgot_{ip}", max_requests=5, window_seconds=60):
        return jsonify({'error': 'Too many requests. Please try again in a few minutes.'}), 429

    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()

    if not email:
        return jsonify({'error': 'Please enter your registered email address.'}), 400

    generic_message = "If an account with that email exists, a 6-digit verification code has been sent."
    db = get_db()
    user = db.execute("SELECT id, email FROM users WHERE email = ?", (email,)).fetchone()

    debug_code = None
    if user:
        # Generate 6-digit code
        raw_code = f"{secrets.randbelow(900000) + 100000:06d}"
        code_hash = hash_reset_code(raw_code)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=Config.RESET_CODE_EXPIRE_MINUTES)

        # Invalidate any prior active codes
        db.execute(
            "UPDATE password_reset_codes SET used_at = CURRENT_TIMESTAMP WHERE user_id = ? AND used_at IS NULL",
            (user['id'],)
        )

        db.execute(
            """
            INSERT INTO password_reset_codes (user_id, code_hash, expires_at, created_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (user['id'], code_hash, expires_at.strftime('%Y-%m-%d %H:%M:%S'))
        )
        db.commit()

        # In dev mode, return the code for testing convenience and log to console
        debug_code = raw_code
        print(f"[SECURITY LOG] Password reset code generated for {email}: {raw_code}")

    res = {'message': generic_message}
    if debug_code and Config.DEBUG:
        res['dev_verification_code'] = debug_code

    return jsonify(res), 200

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    ip = request.remote_addr or 'unknown'
    if not check_rate_limit(f"reset_{ip}", max_requests=10, window_seconds=60):
        return jsonify({'error': 'Too many reset attempts. Please wait a minute and try again.'}), 429

    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    code = data.get('code', '').strip()
    new_password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')

    if not email or not code or not new_password:
        return jsonify({'error': 'Please fill in all fields.'}), 400

    if new_password != confirm_password:
        return jsonify({'error': 'Passwords do not match.'}), 400

    valid_pwd, pwd_err = validate_password_strength(new_password)
    if not valid_pwd:
        return jsonify({'error': pwd_err}), 400

    db = get_db()
    user = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if not user:
        return jsonify({'error': 'Invalid or expired verification code.'}), 400

    # Find valid unused code
    now_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    reset_entry = db.execute(
        """
        SELECT id, code_hash, expires_at FROM password_reset_codes
        WHERE user_id = ? AND used_at IS NULL AND expires_at > ?
        ORDER BY created_at DESC LIMIT 1
        """,
        (user['id'], now_str)
    ).fetchone()

    if not reset_entry:
        return jsonify({'error': 'Verification code expired or already used. Please request a new code.'}), 400

    if not verify_reset_code_hash(code, reset_entry['code_hash']):
        return jsonify({'error': 'Invalid verification code.'}), 400

    # Mark code as used
    db.execute(
        "UPDATE password_reset_codes SET used_at = CURRENT_TIMESTAMP WHERE id = ?",
        (reset_entry['id'],)
    )

    # Update password hash
    new_hash = generate_password_hash(new_password)
    db.execute(
        "UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (new_hash, user['id'])
    )
    db.commit()

    return jsonify({'message': 'Your password has been successfully reset. You can now log in ❤️'}), 200
