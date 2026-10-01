from flask import Blueprint, jsonify, g
from backend.database import get_db
from backend.auth import require_auth
from backend.storage import StorageService
from backend.security import can_user_access_memory

media_bp = Blueprint('media', __name__, url_prefix='/api')

@media_bp.route('/media/<storage_key>', methods=['GET'])
@require_auth
def get_media(storage_key: str):
    """
    Authorized streaming endpoint for private photos and videos.
    Enforces server-side authorization check before serving any byte.
    """
    user_id = g.current_user['id']
    db = get_db()
    memory_row = db.execute("SELECT * FROM memories WHERE storage_key = ?", (storage_key,)).fetchone()

    if not memory_row:
        return jsonify({'error': 'Media not found.'}), 404

    memory = dict(memory_row)
    if not can_user_access_memory(user_id, memory, db):
        return jsonify({'error': "This media is private. You don't have permission to access it."}), 403

    file_path = StorageService.find_media_path(storage_key)
    if not file_path:
        return jsonify({'error': 'Physical media file missing.'}), 404

    return StorageService.stream_file(file_path)

@media_bp.route('/media/thumbnail/<thumbnail_key>', methods=['GET'])
@require_auth
def get_thumbnail(thumbnail_key: str):
    """
    Authorized streaming endpoint for memory thumbnails.
    """
    user_id = g.current_user['id']
    db = get_db()
    # Try finding memory by thumbnail_key or storage_key prefix
    memory_row = db.execute(
        "SELECT * FROM memories WHERE thumbnail_key = ? OR storage_key = ?",
        (thumbnail_key, thumbnail_key.replace('_thumb', ''))
    ).fetchone()

    if not memory_row:
        return jsonify({'error': 'Thumbnail not found.'}), 404

    memory = dict(memory_row)
    if not can_user_access_memory(user_id, memory, db):
        return jsonify({'error': "This media is private. You don't have permission to view this thumbnail."}), 403

    file_path = StorageService.find_thumbnail_path(thumbnail_key)
    if not file_path:
        return jsonify({'error': 'Physical thumbnail file missing.'}), 404

    return StorageService.stream_file(file_path)

@media_bp.route('/avatar/<avatar_key>', methods=['GET'])
def get_avatar(avatar_key: str):
    """Streams user profile avatar."""
    file_path = StorageService.find_avatar_path(avatar_key)
    if not file_path:
        return jsonify({'error': 'Avatar not found.'}), 404

    return StorageService.stream_file(file_path)
