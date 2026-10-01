from flask import Blueprint, jsonify, g
from backend.database import get_db
from backend.auth import require_auth

notification_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')

@notification_bp.route('', methods=['GET'])
@require_auth
def get_notifications():
    """Returns list of notifications and unread count for current user."""
    user_id = g.current_user['id']
    db = get_db()

    rows = db.execute(
        """
        SELECT id, type, reference_id, message, is_read, created_at
        FROM notifications
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 50
        """,
        (user_id,)
    ).fetchall()

    unread_count = db.execute(
        "SELECT COUNT(*) AS count FROM notifications WHERE user_id = ? AND is_read = 0",
        (user_id,)
    ).fetchone()['count']

    notifications = [dict(r) for r in rows]
    return jsonify({
        'notifications': notifications,
        'unread_count': unread_count
    }), 200

@notification_bp.route('/<int:notification_id>/read', methods=['PUT'])
@require_auth
def mark_read(notification_id: int):
    """Marks a single notification as read."""
    user_id = g.current_user['id']
    db = get_db()
    db.execute(
        "UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?",
        (notification_id, user_id)
    )
    db.commit()
    return jsonify({'message': 'Notification marked as read.'}), 200

@notification_bp.route('/read-all', methods=['PUT'])
@require_auth
def mark_all_read():
    """Marks all notifications as read for current user."""
    user_id = g.current_user['id']
    db = get_db()
    db.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (user_id,))
    db.commit()
    return jsonify({'message': 'All notifications marked as read.'}), 200
