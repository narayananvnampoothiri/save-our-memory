from flask import Blueprint, request, jsonify, g
from backend.database import get_db
from backend.auth import require_auth
from backend.security import sanitize_user

connection_bp = Blueprint('connections', __name__, url_prefix='/api/connections')

@connection_bp.route('', methods=['GET'])
@require_auth
def get_connections():
    """Returns accepted connections, incoming pending requests, and outgoing sent requests."""
    user_id = g.current_user['id']
    db = get_db()

    # Accepted connections
    accepted_rows = db.execute(
        """
        SELECT c.id AS connection_id, c.created_at AS connected_at,
               u.id AS user_id, u.name, u.username, u.profile_picture, u.bio
        FROM connections c
        JOIN users u ON (u.id = CASE WHEN c.requester_id = ? THEN c.receiver_id ELSE c.requester_id END)
        WHERE (c.requester_id = ? OR c.receiver_id = ?)
          AND c.status = 'accepted'
        ORDER BY c.updated_at DESC
        """,
        (user_id, user_id, user_id)
    ).fetchall()

    accepted = []
    for r in accepted_rows:
        accepted.append({
            'connection_id': r['connection_id'],
            'connected_at': str(r['connected_at']),
            'user': sanitize_user({
                'id': r['user_id'],
                'name': r['name'],
                'username': r['username'],
                'profile_picture': r['profile_picture'],
                'bio': r['bio']
            })
        })

    # Incoming pending requests
    received_rows = db.execute(
        """
        SELECT c.id AS connection_id, c.created_at,
               u.id AS user_id, u.name, u.username, u.profile_picture, u.bio
        FROM connections c
        JOIN users u ON u.id = c.requester_id
        WHERE c.receiver_id = ? AND c.status = 'pending'
        ORDER BY c.created_at DESC
        """,
        (user_id,)
    ).fetchall()

    received = []
    for r in received_rows:
        received.append({
            'connection_id': r['connection_id'],
            'created_at': str(r['created_at']),
            'requester': sanitize_user({
                'id': r['user_id'],
                'name': r['name'],
                'username': r['username'],
                'profile_picture': r['profile_picture'],
                'bio': r['bio']
            })
        })

    # Outgoing sent requests
    sent_rows = db.execute(
        """
        SELECT c.id AS connection_id, c.created_at,
               u.id AS user_id, u.name, u.username, u.profile_picture, u.bio
        FROM connections c
        JOIN users u ON u.id = c.receiver_id
        WHERE c.requester_id = ? AND c.status = 'pending'
        ORDER BY c.created_at DESC
        """,
        (user_id,)
    ).fetchall()

    sent = []
    for r in sent_rows:
        sent.append({
            'connection_id': r['connection_id'],
            'created_at': str(r['created_at']),
            'receiver': sanitize_user({
                'id': r['user_id'],
                'name': r['name'],
                'username': r['username'],
                'profile_picture': r['profile_picture'],
                'bio': r['bio']
            })
        })

    return jsonify({
        'accepted': accepted,
        'received': received,
        'sent': sent
    }), 200

@connection_bp.route('/request', methods=['POST'])
@require_auth
def send_connection_request():
    """Sends a connection request to another user."""
    user_id = g.current_user['id']
    data = request.get_json() or {}
    target_user_id = data.get('user_id')

    if not target_user_id or int(target_user_id) == user_id:
        return jsonify({'error': 'Invalid recipient for connection request.'}), 400

    target_user_id = int(target_user_id)
    db = get_db()

    target_user = db.execute("SELECT id, name FROM users WHERE id = ?", (target_user_id,)).fetchone()
    if not target_user:
        return jsonify({'error': 'Target user does not exist.'}), 404

    # Check if a connection or request already exists
    existing = db.execute(
        """
        SELECT * FROM connections
        WHERE (requester_id = ? AND receiver_id = ?)
           OR (requester_id = ? AND receiver_id = ?)
        """,
        (user_id, target_user_id, target_user_id, user_id)
    ).fetchone()

    if existing:
        if existing['status'] == 'accepted':
            return jsonify({'error': 'You are already connected with this user.'}), 409
        elif existing['status'] == 'pending':
            if existing['requester_id'] == user_id:
                return jsonify({'error': 'Connection request is already pending.'}), 409
            else:
                # Other person already sent a request to you! Automatically accept it.
                db.execute(
                    "UPDATE connections SET status = 'accepted', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (existing['id'],)
                )
                db.execute(
                    """
                    INSERT INTO notifications (user_id, type, reference_id, message, created_at)
                    VALUES (?, 'connection_accepted', ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (target_user_id, existing['id'], f"{g.current_user['name']} accepted your connection request ❤️")
                )
                db.commit()
                return jsonify({'message': f'You are now connected with {target_user["name"]} ❤️'}), 200
        else: # rejected, reopen as pending
            db.execute(
                """
                UPDATE connections
                SET requester_id = ?, receiver_id = ?, status = 'pending', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (user_id, target_user_id, existing['id'])
            )
            connection_id = existing['id']
    else:
        cursor = db.execute(
            """
            INSERT INTO connections (requester_id, receiver_id, status, created_at, updated_at)
            VALUES (?, ?, 'pending', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (user_id, target_user_id)
        )
        connection_id = cursor.lastrowid

    # Create notification for target user
    db.execute(
        """
        INSERT INTO notifications (user_id, type, reference_id, message, created_at)
        VALUES (?, 'connection_request', ?, ?, CURRENT_TIMESTAMP)
        """,
        (target_user_id, connection_id, f"{g.current_user['name']} wants to connect with you ❤️")
    )
    db.commit()

    return jsonify({'message': 'Your connection request was sent ❤️'}), 201

@connection_bp.route('/<int:connection_id>/accept', methods=['POST'])
@require_auth
def accept_request(connection_id: int):
    """Accepts an incoming connection request."""
    user_id = g.current_user['id']
    db = get_db()
    conn = db.execute("SELECT * FROM connections WHERE id = ?", (connection_id,)).fetchone()

    if not conn:
        return jsonify({'error': 'Connection request not found.'}), 404

    if conn['receiver_id'] != user_id:
        return jsonify({'error': 'You do not have permission to accept this request.'}), 403

    db.execute(
        "UPDATE connections SET status = 'accepted', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (connection_id,)
    )

    # Notify requester
    db.execute(
        """
        INSERT INTO notifications (user_id, type, reference_id, message, created_at)
        VALUES (?, 'connection_accepted', ?, ?, CURRENT_TIMESTAMP)
        """,
        (conn['requester_id'], connection_id, f"{g.current_user['name']} accepted your connection request ❤️")
    )
    db.commit()

    return jsonify({'message': 'Connection request accepted ❤️'}), 200

@connection_bp.route('/<int:connection_id>/reject', methods=['POST'])
@require_auth
def reject_request(connection_id: int):
    """Rejects an incoming connection request."""
    user_id = g.current_user['id']
    db = get_db()
    conn = db.execute("SELECT * FROM connections WHERE id = ?", (connection_id,)).fetchone()

    if not conn:
        return jsonify({'error': 'Connection request not found.'}), 404

    if conn['receiver_id'] != user_id:
        return jsonify({'error': 'You do not have permission to reject this request.'}), 403

    db.execute("UPDATE connections SET status = 'rejected', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (connection_id,))
    db.commit()

    return jsonify({'message': 'Connection request declined.'}), 200

@connection_bp.route('/<int:connection_id>/cancel', methods=['DELETE'])
@require_auth
def cancel_request(connection_id: int):
    """Cancels a pending sent connection request."""
    user_id = g.current_user['id']
    db = get_db()
    conn = db.execute("SELECT * FROM connections WHERE id = ?", (connection_id,)).fetchone()

    if not conn:
        return jsonify({'error': 'Connection request not found.'}), 404

    if conn['requester_id'] != user_id:
        return jsonify({'error': 'You do not have permission to cancel this request.'}), 403

    db.execute("DELETE FROM connections WHERE id = ?", (connection_id,))
    db.commit()

    return jsonify({'message': 'Connection request canceled.'}), 200

@connection_bp.route('/<int:connection_id>/remove', methods=['DELETE'])
@require_auth
def remove_connection(connection_id: int):
    """
    Removes an active connection and immediately revokes all memory permissions
    shared between the two users.
    """
    user_id = g.current_user['id']
    db = get_db()
    conn = db.execute("SELECT * FROM connections WHERE id = ?", (connection_id,)).fetchone()

    if not conn:
        return jsonify({'error': 'Connection not found.'}), 404

    if conn['requester_id'] != user_id and conn['receiver_id'] != user_id:
        return jsonify({'error': 'You do not have permission to remove this connection.'}), 403

    other_user_id = conn['receiver_id'] if conn['requester_id'] == user_id else conn['requester_id']

    # Delete connection
    db.execute("DELETE FROM connections WHERE id = ?", (connection_id,))

    # Clean up selective memory permissions in both directions
    db.execute(
        """
        DELETE FROM memory_permissions
        WHERE (user_id = ? AND memory_id IN (SELECT id FROM memories WHERE user_id = ?))
           OR (user_id = ? AND memory_id IN (SELECT id FROM memories WHERE user_id = ?))
        """,
        (user_id, other_user_id, other_user_id, user_id)
    )

    db.commit()
    return jsonify({'message': 'Connection removed and memory access revoked.'}), 200
