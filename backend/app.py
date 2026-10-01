import os
import sys
from pathlib import Path

# Ensure root directory is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from flask import Flask, jsonify, send_from_directory, request, g
from backend.config import Config
from backend.database import init_db, close_db, get_db
from backend.security import add_security_headers, sanitize_user
from backend.auth import require_auth

# Import Blueprints
from backend.routes.auth_routes import auth_bp
from backend.routes.memory_routes import memory_bp
from backend.routes.media_routes import media_bp
from backend.routes.shared_routes import shared_bp
from backend.routes.connection_routes import connection_bp
from backend.routes.user_routes import user_bp
from backend.routes.notification_routes import notification_bp

def create_app():
    frontend_dir = BASE_DIR / 'frontend'
    app = Flask(__name__, static_folder=str(frontend_dir), static_url_path='')
    app.config.from_mapping(
        SECRET_KEY=Config.SECRET_KEY,
        MAX_CONTENT_LENGTH=Config.MAX_CONTENT_LENGTH
    )

    # Initialize storage & database
    Config.ensure_directories()
    init_db()

    # Tear-down database connection
    app.teardown_appcontext(close_db)

    # Attach security headers
    @app.after_request
    def apply_security_headers(response):
        return add_security_headers(response)

    # Register API Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(memory_bp)
    app.register_blueprint(media_bp)
    app.register_blueprint(shared_bp)
    app.register_blueprint(connection_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(notification_bp)

    # Dashboard aggregate stats endpoint
    @app.route('/api/dashboard/stats', methods=['GET'])
    @require_auth
    def get_dashboard_stats():
        user_id = g.current_user['id']
        db = get_db()

        # Counts
        photo_count = db.execute("SELECT COUNT(*) AS c FROM memories WHERE user_id = ? AND media_type = 'photo'", (user_id,)).fetchone()['c']
        video_count = db.execute("SELECT COUNT(*) AS c FROM memories WHERE user_id = ? AND media_type = 'video'", (user_id,)).fetchone()['c']

        conn_count = db.execute(
            """
            SELECT COUNT(*) AS c FROM connections
            WHERE (requester_id = ? OR receiver_id = ?) AND status = 'accepted'
            """,
            (user_id, user_id)
        ).fetchone()['c']

        # Recent memories by memory_date
        recent_by_date = db.execute(
            """
            SELECT id, media_type, storage_key, thumbnail_key, title, description, memory_date, location, privacy, uploaded_at
            FROM memories
            WHERE user_id = ?
            ORDER BY memory_date DESC, id DESC
            LIMIT 6
            """,
            (user_id,)
        ).fetchall()

        # Recently uploaded memories
        recently_uploaded = db.execute(
            """
            SELECT id, media_type, storage_key, thumbnail_key, title, description, memory_date, location, privacy, uploaded_at
            FROM memories
            WHERE user_id = ?
            ORDER BY uploaded_at DESC, id DESC
            LIMIT 6
            """,
            (user_id,)
        ).fetchall()

        # Connected people preview
        connected_people_rows = db.execute(
            """
            SELECT u.id, u.name, u.username, u.profile_picture, u.bio
            FROM connections c
            JOIN users u ON (u.id = CASE WHEN c.requester_id = ? THEN c.receiver_id ELSE c.requester_id END)
            WHERE (c.requester_id = ? OR c.receiver_id = ?) AND c.status = 'accepted'
            LIMIT 8
            """,
            (user_id, user_id, user_id)
        ).fetchall()

        return jsonify({
            'photo_count': photo_count,
            'video_count': video_count,
            'connection_count': conn_count,
            'recent_memories': [dict(r) for r in recent_by_date],
            'recently_uploaded': [dict(r) for r in recently_uploaded],
            'connected_people': [sanitize_user(dict(r)) for r in connected_people_rows]
        }), 200

    # Frontend SPA routing
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        if path and (frontend_dir / path).is_file():
            return send_from_directory(frontend_dir, path)
        return send_from_directory(frontend_dir, 'index.html')

    # Error Handlers
    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Resource not found.'}), 404
        return send_from_directory(frontend_dir, 'index.html')

    @app.errorhandler(413)
    def file_too_large(e):
        return jsonify({'error': 'File is too large. Maximum size is 100MB.'}), 413

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({'error': 'A server error occurred. Please try again later.'}), 500

    return app

app = create_app()

if __name__ == '__main__':
    print(f"❤️ Save Our Memory server starting on http://{Config.HOST}:{Config.PORT}")
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
