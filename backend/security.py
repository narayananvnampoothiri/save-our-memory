from backend.database import get_db

def can_user_access_memory(user_id: int, memory: dict, db=None) -> bool:
    """
    Strict server-side authorization check for viewing a memory or its media.
    Rules:
      1. Owner always has access.
      2. If privacy is 'private', only owner has access.
      3. If privacy is 'connections', viewer must have an 'accepted' connection with owner.
      4. If privacy is 'selected', viewer must be explicitly listed in memory_permissions.
    """
    if not user_id or not memory:
        return False

    owner_id = memory.get('user_id')
    if owner_id == user_id:
        return True

    privacy = memory.get('privacy', 'private')
    if privacy == 'private':
        return False

    db = db or get_db()

    if privacy == 'connections':
        # Verify mutual accepted connection
        conn = db.execute(
            """
            SELECT 1 FROM connections
            WHERE ((requester_id = ? AND receiver_id = ?) OR (requester_id = ? AND receiver_id = ?))
              AND status = 'accepted'
            """,
            (user_id, owner_id, owner_id, user_id)
        ).fetchone()
        return bool(conn)

    if privacy == 'selected':
        # Verify specific explicit permission
        perm = db.execute(
            """
            SELECT 1 FROM memory_permissions
            WHERE memory_id = ? AND user_id = ?
            """,
            (memory.get('id'), user_id)
        ).fetchone()
        return bool(perm)

    return False

def sanitize_user(user_dict: dict, is_self: bool = False) -> dict:
    """
    Sanitizes user dictionary to prevent accidental exposure of emails or password hashes.
    Only the user themselves can see their registered email address.
    """
    if not user_dict:
        return {}

    clean = {
        'id': user_dict.get('id'),
        'name': user_dict.get('name'),
        'username': user_dict.get('username'),
        'profile_picture': user_dict.get('profile_picture'),
        'bio': user_dict.get('bio'),
        'created_at': str(user_dict.get('created_at', ''))
    }

    if is_self:
        clean['email'] = user_dict.get('email')

    return clean

def add_security_headers(response):
    """Adds secure HTTP headers to all responses."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response
