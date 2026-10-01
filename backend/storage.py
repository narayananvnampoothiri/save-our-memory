import os
import uuid
import mimetypes
from pathlib import Path
from flask import request, Response
from PIL import Image, ImageOps
from backend.config import Config

class StorageService:
    @staticmethod
    def is_valid_image(data: bytes, ext: str) -> bool:
        """Inspects magic bytes for image integrity."""
        if ext in ('.jpg', '.jpeg'):
            return data.startswith(b'\xff\xd8\xff')
        elif ext == '.png':
            return data.startswith(b'\x89PNG\r\n\x1a\n')
        elif ext == '.gif':
            return data.startswith(b'GIF87a') or data.startswith(b'GIF89a')
        elif ext == '.webp':
            return data.startswith(b'RIFF') and len(data) >= 12 and data[8:12] == b'WEBP'
        return False

    @staticmethod
    def is_valid_video(data: bytes, ext: str) -> bool:
        """Inspects magic bytes for video integrity."""
        if ext in ('.mp4', '.mov'):
            # Check for 'ftyp' or 'moov' atom in first 64 bytes
            return b'ftyp' in data[:64] or b'moov' in data[:64] or len(data) > 8
        elif ext == '.webm':
            # Matroska / EBML header
            return data.startswith(b'\x1a\x45\xdf\xa3')
        return False

    @staticmethod
    def save_media(file_storage, media_type: str) -> tuple[str, str | None, str]:
        """
        Saves uploaded file into private storage with a unique UUID key.
        Returns: (storage_key, thumbnail_key, file_extension)
        """
        Config.ensure_directories()
        filename = file_storage.filename or 'upload'
        ext = Path(filename).suffix.lower()

        # Validate extension
        if media_type == 'photo':
            if ext not in Config.ALLOWED_IMAGE_EXTENSIONS:
                raise ValueError(f"Unsupported image format '{ext}'. Allowed: {', '.join(Config.ALLOWED_IMAGE_EXTENSIONS)}")
        elif media_type == 'video':
            if ext not in Config.ALLOWED_VIDEO_EXTENSIONS:
                raise ValueError(f"Unsupported video format '{ext}'. Allowed: {', '.join(Config.ALLOWED_VIDEO_EXTENSIONS)}")
        else:
            raise ValueError(f"Invalid media type '{media_type}'")

        file_bytes = file_storage.read()
        if len(file_bytes) == 0:
            raise ValueError("Uploaded file is empty.")

        # Validate magic bytes
        if media_type == 'photo' and not StorageService.is_valid_image(file_bytes, ext):
            raise ValueError("File content does not match image signature.")
        elif media_type == 'video' and not StorageService.is_valid_video(file_bytes, ext):
            raise ValueError("File content does not match video signature.")

        storage_key = uuid.uuid4().hex
        media_filename = f"{storage_key}{ext}"
        media_path = Config.MEDIA_DIR / media_filename

        with open(media_path, 'wb') as f:
            f.write(file_bytes)

        # Generate thumbnail for photos
        thumbnail_key = None
        if media_type == 'photo':
            try:
                thumbnail_key = f"{storage_key}_thumb"
                thumb_filename = f"{thumbnail_key}.webp"
                thumb_path = Config.THUMBNAIL_DIR / thumb_filename

                from io import BytesIO
                with Image.open(BytesIO(file_bytes)) as img:
                    img = ImageOps.exif_transpose(img)
                    img.thumbnail((500, 500), Image.Resampling.LANCZOS)
                    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                        img.save(thumb_path, 'WEBP', quality=85)
                    else:
                        img.convert('RGB').save(thumb_path, 'WEBP', quality=85)
            except Exception as e:
                # If thumbnail creation fails, fallback to main media
                thumbnail_key = None

        return storage_key, thumbnail_key, ext

    @staticmethod
    def save_avatar(file_storage) -> str:
        """Saves and crops user avatar to square WebP."""
        Config.ensure_directories()
        filename = file_storage.filename or 'avatar'
        ext = Path(filename).suffix.lower()

        if ext not in Config.ALLOWED_IMAGE_EXTENSIONS:
            raise ValueError(f"Unsupported image format '{ext}' for profile picture.")

        file_bytes = file_storage.read()
        if not StorageService.is_valid_image(file_bytes, ext):
            raise ValueError("File content does not match image signature.")

        avatar_key = uuid.uuid4().hex
        avatar_path = Config.AVATAR_DIR / f"{avatar_key}.webp"

        from io import BytesIO
        with Image.open(BytesIO(file_bytes)) as img:
            img = ImageOps.exif_transpose(img)
            # Crop to square
            w, h = img.size
            min_dim = min(w, h)
            left = (w - min_dim) // 2
            top = (h - min_dim) // 2
            img = img.crop((left, top, left + min_dim, top + min_dim))
            img.thumbnail((300, 300), Image.Resampling.LANCZOS)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(avatar_path, 'WEBP', quality=90)

        return avatar_key

    @staticmethod
    def find_media_path(storage_key: str) -> Path | None:
        """Locates media file on disk regardless of extension."""
        for ext in Config.ALLOWED_IMAGE_EXTENSIONS | Config.ALLOWED_VIDEO_EXTENSIONS:
            candidate = Config.MEDIA_DIR / f"{storage_key}{ext}"
            if candidate.is_file():
                return candidate
        return None

    @staticmethod
    def find_thumbnail_path(thumbnail_key: str) -> Path | None:
        """Locates thumbnail file on disk."""
        candidate = Config.THUMBNAIL_DIR / f"{thumbnail_key}.webp"
        if candidate.is_file():
            return candidate
        # Fallback to media if thumbnail doesn't exist
        return StorageService.find_media_path(thumbnail_key.replace('_thumb', ''))

    @staticmethod
    def find_avatar_path(avatar_key: str) -> Path | None:
        """Locates avatar file on disk."""
        candidate = Config.AVATAR_DIR / f"{avatar_key}.webp"
        if candidate.is_file():
            return candidate
        return None

    @staticmethod
    def stream_file(file_path: Path) -> Response:
        """
        Streams file with HTTP 206 Partial Content (Range request) support.
        Vital for video seeking and smooth scrubbing.
        """
        if not file_path or not file_path.is_file():
            return Response("File not found", status=404)

        file_size = file_path.stat().st_size
        mime_type, _ = mimetypes.guess_type(str(file_path))
        mime_type = mime_type or 'application/octet-stream'

        range_header = request.headers.get('Range', None)
        if not range_header:
            def generate():
                with open(file_path, 'rb') as f:
                    while chunk := f.read(65536):
                        yield chunk
            resp = Response(generate(), status=200, mimetype=mime_type)
            resp.headers['Content-Length'] = str(file_size)
            resp.headers['Accept-Ranges'] = 'bytes'
            resp.headers['Cache-Control'] = 'private, max-age=3600'
            return resp

        # Parse Range header: 'bytes=start-end'
        try:
            byte_range = range_header.replace('bytes=', '').strip()
            parts = byte_range.split('-')
            start = int(parts[0]) if parts[0] else 0
            end = int(parts[1]) if parts[1] else file_size - 1
            if end >= file_size:
                end = file_size - 1
            length = end - start + 1
        except Exception:
            return Response("Invalid Range Header", status=416)

        def generate_partial():
            with open(file_path, 'rb') as f:
                f.seek(start)
                bytes_left = length
                while bytes_left > 0:
                    chunk_size = min(bytes_left, 65536)
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    bytes_left -= len(chunk)
                    yield chunk

        resp = Response(generate_partial(), status=206, mimetype=mime_type)
        resp.headers['Content-Range'] = f"bytes {start}-{end}/{file_size}"
        resp.headers['Content-Length'] = str(length)
        resp.headers['Accept-Ranges'] = 'bytes'
        resp.headers['Cache-Control'] = 'private, max-age=3600'
        return resp

    @staticmethod
    def delete_media(storage_key: str, thumbnail_key: str | None = None):
        """Deletes media and thumbnail files safely from disk."""
        media_path = StorageService.find_media_path(storage_key)
        if media_path and media_path.is_file():
            try:
                media_path.unlink()
            except Exception:
                pass

        if thumbnail_key:
            thumb_path = Config.THUMBNAIL_DIR / f"{thumbnail_key}.webp"
            if thumb_path.is_file():
                try:
                    thumb_path.unlink()
                except Exception:
                    pass
