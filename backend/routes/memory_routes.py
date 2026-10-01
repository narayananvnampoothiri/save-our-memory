import json
from flask import Blueprint, request, jsonify, g
from backend.database import get_db
from backend.auth import require_auth
from backend.storage import StorageService
from backend.security import can_user_access_memory, sanitize_user

memory_bp = Blueprint('memories', __name__, url_prefix='/api/memories')

@memory_bp.route('', methods=['GET'])
@require_auth
def get_user_memories():
    """Fetches memories owned by the authenticated user with filtering and sorting."""
    user_id = g.current_user['id']
    media_type = request.args.get('type', 'all').lower()
    year = request.args.get('year', '').strip()
    month = request.args.get('month', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()
    location = request.args.get('location', '').strip()
    sort_option = request.args.get('sort', 'memory_desc').lower()

    query = "SELECT * FROM memories WHERE user_id = ?"
    params = [user_id]

    # Filter by media type
    if media_type in ('photo', 'video'):
        query += " AND media_type = ?"
        params.append(media_type)

    # Filter by year (based on memory_date: YYYY-MM-DD)
    if year.isdigit() and len(year) == 4:
        query += " AND strftime('%Y', memory_date) = ?"
        params.append(year)

    # Filter by month (01 - 12)
    if month.isdigit():
        formatted_month = f"{int(month):02d}"
        query += " AND strftime('%m', memory_date) = ?"
        params.append(formatted_month)

    # Date range filters
    if date_from:
        query += " AND memory_date >= ?"
        params.append(date_from)
    if date_to:
        query += " AND memory_date <= ?"
        params.append(date_to)

    # Location substring filter
    if location:
        query += " AND location LIKE ?"
        params.append(f"%{location}%")

    # Sorting options
    if sort_option == 'memory_asc':
        query += " ORDER BY memory_date ASC, id ASC"
    elif sort_option == 'uploaded_desc':
        query += " ORDER BY uploaded_at DESC, id DESC"
    elif sort_option == 'uploaded_asc':
        query += " ORDER BY uploaded_at ASC, id ASC"
    else:  # default 'memory_desc'
        query += " ORDER BY memory_date DESC, id DESC"

    db = get_db()
    rows = db.execute(query, params).fetchall()

    memories_list = []
    for row in rows:
        m = dict(row)
        # If privacy is 'selected', fetch permitted users
        if m['privacy'] == 'selected':
            perms = db.execute(
                """
                SELECT u.id, u.name, u.username, u.profile_picture
                FROM memory_permissions mp
                JOIN users u ON u.id = mp.user_id
                WHERE mp.memory_id = ?
                """,
                (m['id'],)
            ).fetchall()
            m['permitted_users'] = [sanitize_user(dict(p)) for p in perms]
        else:
            m['permitted_users'] = []
        memories_list.append(m)

    return jsonify({'memories': memories_list}), 200

@memory_bp.route('', methods=['POST'])
@require_auth
def create_memory():
    """Uploads and creates a new memory."""
    user_id = g.current_user['id']

    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded. Please select a photo or video.'}), 400

    file = request.files['file']
    media_type = request.form.get('media_type', '').strip().lower()
    memory_date = request.form.get('memory_date', '').strip()
    title = request.form.get('title', '').strip()
    location = request.form.get('location', '').strip()
    description = request.form.get('description', '').strip()
    privacy = request.form.get('privacy', 'private').strip().lower()
    selected_users_raw = request.form.get('selected_users', '[]')

    if not media_type or media_type not in ('photo', 'video'):
        return jsonify({'error': 'Media type must be either "photo" or "video".'}), 400

    if not memory_date:
        return jsonify({'error': 'Please enter the date when this memory took place.'}), 400

    if privacy not in ('private', 'connections', 'selected'):
        privacy = 'private'

    selected_user_ids = []
    if privacy == 'selected':
        try:
            selected_user_ids = json.loads(selected_users_raw)
            if not isinstance(selected_user_ids, list):
                selected_user_ids = []
            selected_user_ids = [int(uid) for uid in selected_user_ids]
        except Exception:
            selected_user_ids = []

    try:
        storage_key, thumbnail_key, ext = StorageService.save_media(file, media_type)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to save media file. Please try again.'}), 500

    db = get_db()
    cursor = db.execute(
        """
        INSERT INTO memories (
            user_id, media_type, storage_key, thumbnail_key,
            title, description, memory_date, location,
            privacy, uploaded_at, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        (user_id, media_type, storage_key, thumbnail_key, title, description, memory_date, location, privacy)
    )
    memory_id = cursor.lastrowid

    # Handle selective permissions
    if privacy == 'selected' and selected_user_ids:
        for suid in set(selected_user_ids):
            # Only allow adding users who have an accepted connection
            is_connected = db.execute(
                """
                SELECT 1 FROM connections
                WHERE ((requester_id = ? AND receiver_id = ?) OR (requester_id = ? AND receiver_id = ?))
                  AND status = 'accepted'
                """,
                (user_id, suid, suid, user_id)
            ).fetchone()

            if is_connected:
                db.execute(
                    "INSERT OR IGNORE INTO memory_permissions (memory_id, user_id, created_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                    (memory_id, suid)
                )
                # Send notification to shared user
                db.execute(
                    """
                    INSERT INTO notifications (user_id, type, reference_id, message, created_at)
                    VALUES (?, 'memory_shared', ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (suid, memory_id, f"{g.current_user['name']} shared a memory with you: '{title or 'A precious moment'}' ❤️")
                )

    db.commit()

    created_row = db.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
    memory_dict = dict(created_row)

    return jsonify({
        'message': 'Your memory was saved ❤️',
        'memory': memory_dict
    }), 201

@memory_bp.route('/<int:memory_id>', methods=['GET'])
@require_auth
def get_memory(memory_id: int):
    """Fetches details for a single memory with strict authorization verification."""
    user_id = g.current_user['id']
    db = get_db()
    row = db.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()

    if not row:
        return jsonify({'error': 'Memory not found.'}), 404

    memory = dict(row)
    if not can_user_access_memory(user_id, memory, db):
        return jsonify({'error': "This memory is private. You don't have permission to view it."}), 403

    # Include owner public profile
    owner = db.execute("SELECT id, name, username, profile_picture FROM users WHERE id = ?", (memory['user_id'],)).fetchone()
    memory['owner'] = sanitize_user(dict(owner)) if owner else None
    memory['is_owner'] = (memory['user_id'] == user_id)

    # If owner, include permitted users
    if memory['is_owner'] and memory['privacy'] == 'selected':
        perms = db.execute(
            """
            SELECT u.id, u.name, u.username, u.profile_picture
            FROM memory_permissions mp
            JOIN users u ON u.id = mp.user_id
            WHERE mp.memory_id = ?
            """,
            (memory_id,)
        ).fetchall()
        memory['permitted_users'] = [sanitize_user(dict(p)) for p in perms]
    else:
        memory['permitted_users'] = []

    return jsonify({'memory': memory}), 200

@memory_bp.route('/<int:memory_id>', methods=['PUT'])
@require_auth
def update_memory(memory_id: int):
    """Updates metadata and privacy of a memory (owner only)."""
    user_id = g.current_user['id']
    db = get_db()
    row = db.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()

    if not row:
        return jsonify({'error': 'Memory not found.'}), 404

    if row['user_id'] != user_id:
        return jsonify({'error': 'Only the owner can edit this memory.'}), 403

    data = request.get_json() or {}
    title = data.get('title', row['title']).strip()
    description = data.get('description', row['description']).strip()
    memory_date = data.get('memory_date', row['memory_date']).strip()
    location = data.get('location', row['location']).strip()
    new_privacy = data.get('privacy', row['privacy']).strip().lower()

    if new_privacy not in ('private', 'connections', 'selected'):
        new_privacy = row['privacy']

    db.execute(
        """
        UPDATE memories
        SET title = ?, description = ?, memory_date = ?, location = ?, privacy = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (title, description, memory_date, location, new_privacy, memory_id)
    )

    # Update selected user permissions if specified
    if 'selected_users' in data:
        selected_user_ids = data.get('selected_users', [])
        # Clear existing permissions for this memory
        db.execute("DELETE FROM memory_permissions WHERE memory_id = ?", (memory_id,))

        if new_privacy == 'selected' and isinstance(selected_user_ids, list):
            for suid in set(selected_user_ids):
                # Verify connected
                is_connected = db.execute(
                    """
                    SELECT 1 FROM connections
                    WHERE ((requester_id = ? AND receiver_id = ?) OR (requester_id = ? AND receiver_id = ?))
                      AND status = 'accepted'
                    """,
                    (user_id, suid, suid, user_id)
                ).fetchone()
                if is_connected:
                    db.execute(
                        "INSERT OR IGNORE INTO memory_permissions (memory_id, user_id, created_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                        (memory_id, suid)
                    )

    db.commit()

    updated_row = db.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
    return jsonify({'message': 'Memory updated successfully ❤️', 'memory': dict(updated_row)}), 200

@memory_bp.route('/<int:memory_id>', methods=['DELETE'])
@require_auth
def delete_memory(memory_id: int):
    """Deletes a memory and its physical files (owner only)."""
    user_id = g.current_user['id']
    db = get_db()
    row = db.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()

    if not row:
        return jsonify({'error': 'Memory not found.'}), 404

    if row['user_id'] != user_id:
        return jsonify({'error': 'Only the owner can delete this memory.'}), 403

    storage_key = row['storage_key']
    thumbnail_key = row['thumbnail_key']

    # Delete database record (cascading deletes memory_permissions)
    db.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
    db.commit()

    # Safely remove media files from disk
    StorageService.delete_media(storage_key, thumbnail_key)

    return jsonify({'message': 'Your memory was deleted.'}), 200
