import os
from pathlib import Path

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

def load_env(env_path: Path):
    """Simple parser for .env files without external dependencies."""
    if not env_path.is_file():
        return
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, val = line.split('=', 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key not in os.environ:
                os.environ[key] = val

# Load .env if present
load_env(BASE_DIR / '.env')

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-dev-secret-key-save-our-memory')
    PORT = int(os.environ.get('PORT', 5000))
    HOST = os.environ.get('HOST', '127.0.0.1')
    DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 't')
    
    # Storage settings
    STORAGE_DIR = BASE_DIR / os.environ.get('STORAGE_DIR', 'storage')
    MEDIA_DIR = STORAGE_DIR / 'media'
    THUMBNAIL_DIR = STORAGE_DIR / 'thumbnails'
    AVATAR_DIR = STORAGE_DIR / 'avatars'
    DATABASE_PATH = BASE_DIR / os.environ.get('DATABASE_PATH', 'storage/database.sqlite')
    
    # Upload limits: 100 MB max request body
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 100 * 1024 * 1024))
    
    # Expiry configurations
    TOKEN_EXPIRE_HOURS = int(os.environ.get('TOKEN_EXPIRE_HOURS', 72))
    RESET_CODE_EXPIRE_MINUTES = int(os.environ.get('RESET_CODE_EXPIRE_MINUTES', 15))
    
    # Allowed formats
    ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
    ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.webm', '.mov'}
    
    @classmethod
    def ensure_directories(cls):
        cls.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        cls.MEDIA_DIR.mkdir(parents=True, exist_ok=True)
        cls.THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)
        cls.AVATAR_DIR.mkdir(parents=True, exist_ok=True)
        cls.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
