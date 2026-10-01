from flask import Blueprint, request, jsonify, g
from backend.database import get_db
from backend.auth import require_auth
from backend.security import sanitize_user

shared_bp = Blueprint('shared', __name__, url_prefix='/api/shared')

@shared_bp.route('', methods=['GET'])
@require_auth
def get_shared_memories():
    """
    Returns all memories shared with the current user by connected partners/friends.
    Only memories that are explicitly:
      a) privacy = 'connections' from accepted connections, OR
      b) privacy = 'selected' with an explicit record in memory_permissions for this user.
    """
    user_id = g.current_user['id']
    media_type = request.args.get('type', 'all').lower()
    year = request.args.get('year', '').strip()
    month = request.args.get('month', '').strip()
    location = request.args.get('location', '').strip()
    sort_option = request.args.get('sort', 'memory_desc').lower()

    db = get_db()

    # Query all memories shared either via connections privacy or via selected memory_permissions
    query = """
    SELECT m.*, u.id AS owner_id, u.name AS owner_name, u.username AS owner_username, u.profile_picture AS owner_profile_picture
    FROM memories m
    JOIN users u ON u.id = m.user_id
    WHERE m.user_id != ?
      AND (
        -- Case 1: Shared with all accepted connections
        (
            m.privacy = 'connections'
            AND EXISTS (
                SELECT 1 FROM connections c
                WHERE ((c.requester_id = ? AND c.receiver_id = m.user_id) OR (c.requester_id = m.user_id AND c.receiver_id = ?))
                  AND c.status = 'accepted'
            )
        )
        OR
        -- Case 2: Specifically selected permission
        (
            m.privacy = 'selected'
            AND EXISTS (
                SELECT 1 FROM memory_permissions mp
                WHERE mp.memory_id = m.id AND mp.user_id = ?
            )
            AND EXISTS (
                SELECT 1 FROM connections c
                WHERE ((c.requester_id = ? AND c.receiver_id = m.user_id) OR (c.requester_id = m.user_id AND c.receiver_id = ?))
                  AND c.status = 'accepted'
            )
        )
      )
    """
    params = [user_id, user_id, user_id, user_id, user_id, user_id]

    if media_type in ('photo', 'video'):
        query += " AND m.media_type = ?"
        params.append(media_type)

    if year.isdigit() and len(year) == 4:
        query += " AND strftime('%Y', m.memory_date) = ?"
        params.append(year)

    if month.isdigit():
        formatted_month = f"{int(month):02d}"
        query += " AND strftime('%m', m.memory_date) = ?"
        params.append(formatted_month)

    if location:
        query += " AND m.location LIKE ?"
        params.append(f"%{location}%")

    if sort_option == 'memory_asc':
        query += " ORDER BY m.memory_date ASC, m.id ASC"
    elif sort_option == 'uploaded_desc':
        query += " ORDER BY m.uploaded_at DESC, m.id DESC"
    elif sort_option == 'uploaded_asc':
        query += " ORDER BY m.uploaded_at ASC, m.id ASC"
    else:
        query += " ORDER BY m.memory_date DESC, m.id DESC"

    rows = db.execute(query, params).fetchall()

    shared_list = []
    for row in rows:
        item = dict(row)
        item['is_owner'] = False
        item['owner'] = {
            'id': item.pop('owner_id'),
            'name': item.pop('owner_name'),
            'username': item.pop('owner_username'),
            'profile_picture': item.pop('owner_profile_picture')
        }
        shared_list.append(item)

    return jsonify({'memories': shared_list}), 200
