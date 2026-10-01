import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Ensure root directory is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from PIL import Image, ImageDraw, ImageFont
from werkzeug.security import generate_password_hash
from backend.config import Config
from backend.database import get_direct_db, init_db

def create_sample_photo(storage_key: str, title: str, subtitle: str, bg_color1: tuple, bg_color2: tuple) -> str:
    """Generates a beautiful romantic-aesthetic sample image."""
    width, height = 1200, 900
    img = Image.new("RGB", (width, height), bg_color1)
    draw = ImageDraw.Draw(img)

    # Vertical gradient
    for y in range(height):
        r = int(bg_color1[0] + (bg_color2[0] - bg_color1[0]) * (y / height))
        g = int(bg_color1[1] + (bg_color2[1] - bg_color1[1]) * (y / height))
        b = int(bg_color1[2] + (bg_color2[2] - bg_color1[2]) * (y / height))
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Inner decorative border
    border_margin = 40
    draw.rectangle(
        [(border_margin, border_margin), (width - border_margin, height - border_margin)],
        outline=(255, 255, 255, 160),
        width=3
    )
    draw.rectangle(
        [(border_margin + 8, border_margin + 8), (width - border_margin - 8, height - border_margin - 8)],
        outline=(255, 255, 255, 100),
        width=1
    )

    # Title & text simulation
    # Draw soft glowing center badge
    badge_w, badge_h = 750, 320
    bx0 = (width - badge_w) // 2
    by0 = (height - badge_h) // 2
    draw.rounded_rectangle([(bx0, by0), (bx0 + badge_w, by0 + badge_h)], radius=24, fill=(20, 16, 14, 180), outline=(255, 235, 225, 140), width=2)

    # Decorative icon
    draw.text((width // 2 - 30, by0 + 40), "❤️", fill=(255, 160, 160))
    # Title
    draw.text((bx0 + 60, by0 + 110), title, fill=(255, 245, 240))
    # Subtitle
    draw.text((bx0 + 60, by0 + 190), subtitle, fill=(230, 215, 205))
    draw.text((bx0 + 60, by0 + 240), "SAVE OUR MEMORY VAULT • PRIVATE & TIMELESS", fill=(200, 180, 170))

    # Save media file
    media_path = Config.MEDIA_DIR / f"{storage_key}.jpg"
    img.save(media_path, "JPEG", quality=92)

    # Generate thumbnail
    thumbnail_key = f"{storage_key}_thumb"
    thumb = img.copy()
    thumb.thumbnail((450, 450), Image.Resampling.LANCZOS)
    thumb_path = Config.THUMBNAIL_DIR / f"{thumbnail_key}.webp"
    thumb.save(thumb_path, "WEBP", quality=85)

    return thumbnail_key

def create_sample_video(storage_key: str) -> None:
    """
    Creates a minimal valid MP4 video container file so browsers can load and test
    streaming, range headers, and video player UI.
    """
    # Minimal ftyp box and moov atom representing an MP4 container
    # 32-byte valid MP4 signature
    ftyp_data = (
        b'\x00\x00\x00\x20ftypisom\x00\x00\x02\x00isomiso2avc1mp41'
        b'\x00\x00\x00\x08free'
        b'\x00\x00\x01\x00mdat' + (b'\x00' * 50000)
    )
    media_path = Config.MEDIA_DIR / f"{storage_key}.mp4"
    with open(media_path, 'wb') as f:
        f.write(ftyp_data)

def seed():
    """Seeds the database with users, connections, memories, and permissions."""
    print("🌱 Initializing and seeding 'Save Our Memory'...")
    Config.ensure_directories()
    init_db()
    conn = get_direct_db()

    # Clear existing data for clean idempotent seeding
    conn.execute("DELETE FROM notifications")
    conn.execute("DELETE FROM memory_permissions")
    conn.execute("DELETE FROM memories")
    conn.execute("DELETE FROM connections")
    conn.execute("DELETE FROM password_reset_codes")
    conn.execute("DELETE FROM users")

    # 1. Create Users
    pwd_hash = generate_password_hash("LoveStory2026!")

    # Narayanan
    cur = conn.execute(
        """
        INSERT INTO users (name, username, email, password_hash, bio, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, '2025-10-01 10:00:00', '2025-10-01 10:00:00')
        """,
        ("Narayanan Ram", "narayanan", "narayanan@example.com", pwd_hash, "Documenting our favorite little moments together ✨")
    )
    user_narayanan = cur.lastrowid

    # Anu Maria
    cur = conn.execute(
        """
        INSERT INTO users (name, username, email, password_hash, bio, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, '2025-10-05 11:30:00', '2025-10-05 11:30:00')
        """,
        ("Anu Maria", "anumaria", "anu@example.com", pwd_hash, "Coffee enthusiast, ocean lover & memory keeper 🌊☕")
    )
    user_anu = cur.lastrowid

    # Siddharth
    cur = conn.execute(
        """
        INSERT INTO users (name, username, email, password_hash, bio, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, '2025-11-12 14:15:00', '2025-11-12 14:15:00')
        """,
        ("Siddharth", "sid", "sid@example.com", pwd_hash, "Travel photographer & longtime friend 📷")
    )
    user_sid = cur.lastrowid

    # 2. Connections
    # Narayanan & Anu: Accepted
    conn.execute(
        """
        INSERT INTO connections (requester_id, receiver_id, status, created_at, updated_at)
        VALUES (?, ?, 'accepted', '2025-10-10 12:00:00', '2025-10-10 12:05:00')
        """,
        (user_narayanan, user_anu)
    )

    # Siddharth -> Narayanan: Pending
    conn.execute(
        """
        INSERT INTO connections (requester_id, receiver_id, status, created_at, updated_at)
        VALUES (?, ?, 'pending', '2026-09-18 09:30:00', '2026-09-18 09:30:00')
        """,
        (user_sid, user_narayanan)
    )

    # Notifications
    conn.execute(
        """
        INSERT INTO notifications (user_id, type, reference_id, message, is_read, created_at)
        VALUES (?, 'connection_request', 2, 'Siddharth wants to connect with you ❤️', 0, '2026-09-18 09:30:00')
        """,
        (user_narayanan,)
    )

    # 3. Memories for Narayanan
    # Memory 1: Photo - Selected (shared with Anu)
    k1 = uuid.uuid4().hex
    th1 = create_sample_photo(k1, "First Coffee Date ☕", "Indiranagar, Bangalore • 14 Oct 2025", (110, 55, 45), (45, 25, 20))
    cur = conn.execute(
        """
        INSERT INTO memories (user_id, media_type, storage_key, thumbnail_key, title, description, memory_date, location, privacy, uploaded_at, created_at)
        VALUES (?, 'photo', ?, ?, ?, ?, '2025-10-14', 'Indiranagar, Bangalore', 'selected', '2025-10-15 10:00:00', '2025-10-15 10:00:00')
        """,
        (user_narayanan, k1, th1, "First Coffee Date ☕", "Where it all began. Two cups of cappuccino and four hours of talking that felt like five minutes.")
    )
    m1_id = cur.lastrowid
    # Grant permission to Anu
    conn.execute("INSERT INTO memory_permissions (memory_id, user_id) VALUES (?, ?)", (m1_id, user_anu))

    # Memory 2: Photo - Connections
    k2 = uuid.uuid4().hex
    th2 = create_sample_photo(k2, "Valentine's Sunrise Trip ❤️", "Nandi Hills, Bangalore • 14 Feb 2026", (180, 80, 70), (70, 30, 40))
    conn.execute(
        """
        INSERT INTO memories (user_id, media_type, storage_key, thumbnail_key, title, description, memory_date, location, privacy, uploaded_at, created_at)
        VALUES (?, 'photo', ?, ?, ?, ?, '2026-02-14', 'Nandi Hills, Bangalore', 'connections', '2026-02-14 20:00:00', '2026-02-14 20:00:00')
        """,
        (user_narayanan, k2, th2, "Valentine's Sunrise Trip ❤️", "Woke up at 4 AM to catch the cloud bed and the crimson sunrise together. Absolutely unforgettable.")
    )

    # Memory 3: Photo - Private (Narayanan ONLY)
    k3 = uuid.uuid4().hex
    th3 = create_sample_photo(k3, "Quiet Monsoon Evening at Home 🌧️", "Bangalore, India • 22 Jul 2026", (40, 60, 85), (20, 30, 45))
    conn.execute(
        """
        INSERT INTO memories (user_id, media_type, storage_key, thumbnail_key, title, description, memory_date, location, privacy, uploaded_at, created_at)
        VALUES (?, 'photo', ?, ?, ?, ?, '2026-07-22', 'Bangalore, India', 'private', '2026-07-23 08:30:00', '2026-07-23 08:30:00')
        """,
        (user_narayanan, k3, th3, "Quiet Monsoon Evening at Home 🌧️", "Rain tapping softly on the glass, hot ginger chai, and our favorite vintage records playing.")
    )

    # Memory 4: Video - Selected (shared with Anu)
    k4 = uuid.uuid4().hex
    create_sample_video(k4)
    # Thumbnail for video
    th4 = create_sample_photo(f"{k4}_vthumb", "Road Trip Through Coorg 🚗", "Coorg, Karnataka • 20 Mar 2026", (60, 90, 60), (25, 45, 25))
    cur = conn.execute(
        """
        INSERT INTO memories (user_id, media_type, storage_key, thumbnail_key, title, description, memory_date, location, privacy, uploaded_at, created_at)
        VALUES (?, 'video', ?, ?, ?, ?, '2026-03-20', 'Coorg, Karnataka', 'selected', '2026-03-22 18:00:00', '2026-03-22 18:00:00')
        """,
        (user_narayanan, k4, th4, "Road Trip Through Coorg 🚗", "Singing old acoustic songs through the misty coffee estates with the windows rolled down.")
    )
    m4_id = cur.lastrowid
    conn.execute("INSERT INTO memory_permissions (memory_id, user_id) VALUES (?, ?)", (m4_id, user_anu))

    # Memory 5: Photo - Private
    k5 = uuid.uuid4().hex
    th5 = create_sample_photo(k5, "Personal Journal & Future Letters 💌", "Bangalore • 05 Aug 2026", (70, 50, 40), (30, 20, 15))
    conn.execute(
        """
        INSERT INTO memories (user_id, media_type, storage_key, thumbnail_key, title, description, memory_date, location, privacy, uploaded_at, created_at)
        VALUES (?, 'photo', ?, ?, ?, ?, '2026-08-05', 'Bangalore, India', 'private', '2026-08-05 21:00:00', '2026-08-05 21:00:00')
        """,
        (user_narayanan, k5, th5, "Personal Journal & Future Letters 💌", "My private reflections, dreams, and promises kept safely in this vault.")
    )

    # 4. Memories for Anu Maria
    # Memory 6: Photo - Connections (Narayanan can see in Shared With Me)
    k6 = uuid.uuid4().hex
    th6 = create_sample_photo(k6, "Beach Sunset Walk 🌊", "Palolem Beach, Goa • 18 Jan 2026", (190, 110, 60), (80, 45, 30))
    conn.execute(
        """
        INSERT INTO memories (user_id, media_type, storage_key, thumbnail_key, title, description, memory_date, location, privacy, uploaded_at, created_at)
        VALUES (?, 'photo', ?, ?, ?, ?, '2026-01-18', 'Palolem Beach, Goa', 'connections', '2026-01-19 12:00:00', '2026-01-19 12:00:00')
        """,
        (user_anu, k6, th6, "Beach Sunset Walk 🌊", "Warm waves touching our feet, golden hour sky, and that peaceful feeling when time stands still.")
    )

    # Memory 7: Photo - Selected (shared with Narayanan)
    k7 = uuid.uuid4().hex
    th7 = create_sample_photo(k7, "Surprise Birthday Celebration 🎂", "Bangalore • 12 Apr 2026", (160, 60, 90), (60, 25, 45))
    cur = conn.execute(
        """
        INSERT INTO memories (user_id, media_type, storage_key, thumbnail_key, title, description, memory_date, location, privacy, uploaded_at, created_at)
        VALUES (?, 'photo', ?, ?, ?, ?, '2026-04-12', 'Bangalore', 'selected', '2026-04-13 14:00:00', '2026-04-13 14:00:00')
        """,
        (user_anu, k7, th7, "Surprise Birthday Celebration 🎂", "The expression of pure surprise on his face when everyone shouted surprise! So grateful for this day.")
    )
    m7_id = cur.lastrowid
    conn.execute("INSERT INTO memory_permissions (memory_id, user_id) VALUES (?, ?)", (m7_id, user_narayanan))

    # Memory 8: Photo - Private to Anu (Narayanan CANNOT see)
    k8 = uuid.uuid4().hex
    th8 = create_sample_photo(k8, "Anu's Private Sketchbook 🎨", "Studio • 10 Jun 2026", (80, 70, 90), (35, 30, 45))
    conn.execute(
        """
        INSERT INTO memories (user_id, media_type, storage_key, thumbnail_key, title, description, memory_date, location, privacy, uploaded_at, created_at)
        VALUES (?, 'photo', ?, ?, ?, ?, '2026-06-10', 'Studio', 'private', '2026-06-10 22:00:00', '2026-06-10 22:00:00')
        """,
        (user_anu, k8, th8, "Anu's Private Sketchbook 🎨", "Personal drawings and watercolor drafts.")
    )

    conn.commit()
    conn.close()
    print("✅ Seed complete! Demo accounts ready:")
    print("   1. Narayanan : narayanan / LoveStory2026!")
    print("   2. Anu Maria : anumaria / LoveStory2026!")
    print("   3. Siddharth : sid / LoveStory2026!")

if __name__ == '__main__':
    seed()
