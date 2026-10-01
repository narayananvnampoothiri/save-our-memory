from flask import Blueprint, request, jsonify, g
from backend.database import get_db
from backend.auth import require_auth, validate_username
from backend.storage import StorageService
from backend.security import sanitize_user

import re

user_bp = Blueprint('users', __name__, url_prefix='/api/users')

@user_bp.route('/search', methods=['GET'])
@require_auth
def search_users():
    """
    Searches users by username, full name, or registered email.
    Supports queries with or without '@', whitespace tolerance, and fallback fuzzy matching.
    Strictly protects privacy: emails and private memories are never exposed to other users.
    """
    user_id = g.current_user['id']
    raw_query = request.args.get('q', '').strip()
    clean_query = raw_query.lstrip('@').strip()

    if not clean_query or len(clean_query) < 1:
        return jsonify({'users': []}), 200

    db = get_db()
    search_term = f"%{clean_query}%"
    no_space_term = f"%{clean_query.replace(' ', '')}%"

    rows = db.execute(
        """
        SELECT id, name, username, email, profile_picture, bio, created_at
        FROM users
        WHERE username LIKE ? COLLATE NOCASE
           OR username LIKE ? COLLATE NOCASE
           OR name LIKE ? COLLATE NOCASE
           OR email LIKE ? COLLATE NOCASE
        ORDER BY
            CASE WHEN id = ? THEN 2 ELSE 0 END,
            CASE WHEN username = ? COLLATE NOCASE THEN 0
                 WHEN name = ? COLLATE NOCASE THEN 1
                 WHEN email = ? COLLATE NOCASE THEN 2
                 ELSE 3 END,
            name ASC
        LIMIT 25
        """,
        (search_term, no_space_term, search_term, search_term, user_id, clean_query, clean_query, clean_query)
    ).fetchall()

    # Fallback: If 0 results and query ends in numbers or has typo (e.g. naran111 instead of naran123)
    if not rows and len(clean_query) >= 3:
        base = re.sub(r'\d+$', '', clean_query)
        if len(base) >= 3 and base != clean_query:
            base_term = f"%{base}%"
            rows = db.execute(
                """
                SELECT id, name, username, email, profile_picture, bio, created_at
                FROM users
                WHERE username LIKE ? COLLATE NOCASE
                   OR name LIKE ? COLLATE NOCASE
                   OR email LIKE ? COLLATE NOCASE
                ORDER BY
                    CASE WHEN id = ? THEN 2 ELSE 0 END,
                    name ASC
                LIMIT 25
                """,
                (base_term, base_term, base_term, user_id)
            ).fetchall()

    users_list = []
    for row in rows:
        row_dict = dict(row)
        is_self = (row_dict['id'] == user_id)
        u = sanitize_user(row_dict, is_self=is_self)

        status = 'none'
        connection_id = None
        if is_self:
            status = 'self'
        else:
            conn = db.execute(
                """
                SELECT id, requester_id, receiver_id, status FROM connections
                WHERE (requester_id = ? AND receiver_id = ?)
                   OR (requester_id = ? AND receiver_id = ?)
                """,
                (user_id, u['id'], u['id'], user_id)
            ).fetchone()

            if conn:
                connection_id = conn['id']
                if conn['status'] == 'accepted':
                    status = 'connected'
                elif conn['status'] == 'pending':
                    if conn['requester_id'] == user_id:
                        status = 'pending_outgoing'
                    else:
                        status = 'pending_incoming'

        u['connection_status'] = status
        u['connection_id'] = connection_id
        users_list.append(u)

    return jsonify({'users': users_list}), 200

@user_bp.route('/<int:target_id>', methods=['GET'])
@require_auth
def get_user_profile(target_id: int):
    """Fetches public profile and connection status for a user."""
    user_id = g.current_user['id']
    db = get_db()
    row = db.execute(
        "SELECT id, name, username, profile_picture, bio, created_at FROM users WHERE id = ?",
        (target_id,)
    ).fetchone()

    if not row:
        return jsonify({'error': 'User not found.'}), 404

    is_self = (target_id == user_id)
    u = sanitize_user(dict(row), is_self=is_self)

    # Determine connection status
    conn = db.execute(
        """
        SELECT id, requester_id, receiver_id, status FROM connections
        WHERE (requester_id = ? AND receiver_id = ?)
           OR (requester_id = ? AND receiver_id = ?)
        """,
        (user_id, target_id, target_id, user_id)
    ).fetchone()

    status = 'self' if is_self else 'none'
    connection_id = None
    if conn and not is_self:
        connection_id = conn['id']
        if conn['status'] == 'accepted':
            status = 'connected'
        elif conn['status'] == 'pending':
            status = 'pending_outgoing' if conn['requester_id'] == user_id else 'pending_incoming'

    u['connection_status'] = status
    u['connection_id'] = connection_id

    # If connected or self, provide public memory stats
    if is_self:
        stats = db.execute(
            """
            SELECT
                SUM(CASE WHEN media_type = 'photo' THEN 1 ELSE 0 END) AS total_photos,
                SUM(CASE WHEN media_type = 'video' THEN 1 ELSE 0 END) AS total_videos
            FROM memories WHERE user_id = ?
            """,
            (user_id,)
        ).fetchone()
        u['total_photos'] = stats['total_photos'] or 0
        u['total_videos'] = stats['total_videos'] or 0

    return jsonify({'user': u}), 200

@user_bp.route('/profile', methods=['PUT'])
@require_auth
def update_profile():
    """Updates the authenticated user's profile information."""
    user_id = g.current_user['id']
    db = get_db()

    # Can be multipart or json
    name = request.form.get('name') if request.form else None
    bio = request.form.get('bio') if request.form else None
    username = request.form.get('username') if request.form else None

    if request.is_json:
        data = request.get_json() or {}
        name = data.get('name', name)
        bio = data.get('bio', bio)
        username = data.get('username', username)

    current_user_row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    updated_name = name.strip() if name is not None else current_user_row['name']
    updated_bio = bio.strip() if bio is not None else current_user_row['bio']
    updated_username = username.strip() if username is not None else current_user_row['username']

    if updated_username.lower() != current_user_row['username'].lower():
        valid_u, u_err = validate_username(updated_username)
        if not valid_u:
            return jsonify({'error': u_err}), 400

        existing = db.execute("SELECT id FROM users WHERE username = ? AND id != ?", (updated_username, user_id)).fetchone()
        if existing:
            return jsonify({'error': 'This username is already in use.'}), 409

    profile_picture_key = current_user_row['profile_picture']
    if 'profile_picture' in request.files:
        pic_file = request.files['profile_picture']
        try:
            profile_picture_key = StorageService.save_avatar(pic_file)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception:
            return jsonify({'error': 'Failed to save avatar image.'}), 500

    db.execute(
        """
        UPDATE users
        SET name = ?, username = ?, bio = ?, profile_picture = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (updated_name, updated_username, updated_bio, profile_picture_key, user_id)
    )
    db.commit()

    updated_row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return jsonify({
        'message': 'Profile updated successfully ❤️',
        'user': sanitize_user(dict(updated_row), is_self=True)
    }), 200
