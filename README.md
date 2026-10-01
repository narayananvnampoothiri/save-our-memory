# ❤️ Save Our Memory

> **A Private Digital Memory Sanctuary for Couples, Families, and Close Friends.**  
> Keep your milestones, heartfelt moments, photos, and videos safe, organized, and shared only with the people who matter most.

---

## 🌟 Key Features

- **🛡️ Private & Secure by Design**
  - No public feeds, ads, or algorithms.
  - Three-tier privacy controls per memory:
    - 🔒 **Private**: Only visible to you.
    - 👥 **Connections**: Shared with all your accepted connections.
    - 🎯 **Selected**: Shared exclusively with specifically chosen people.
  - Signed auth sessions & token-protected media streaming.

- **📷 Photos & 🎥 Video Vault**
  - Instant uploads with auto-generated WebP thumbnails for lightning-fast loads.
  - Video streaming support with HTTP 206 partial-content range headers.
  - Chronological memory date tracking with full metadata (location, title, description, memory date).

- **⏳ Interactive Timeline & Filtering**
  - Filter your vault by year, month, media type (photos/videos), or search by location.
  - Dynamic sort options (by memory date or upload time).

- **💌 Shared With Me**
  - View all moments shared with you by partners and loved ones.
  - Instant connection requests, accept/reject flows, and notification badges.

- **🎨 Modern Aesthetic Design**
  - Curated romantic-aesthetic palette with Playfair Display & Plus Jakarta Sans typography.
  - Full Light and Dark mode toggle with persistent preferences.
  - Responsive mobile bottom navigation bar and desktop header.

---

## 🚀 Quick Start Guide

### Option 1: Double-Click (Windows)
Double-click [`start.bat`](file:///c:/Users/nampo/OneDrive/Desktop/GALLERY/start.bat).  
It will automatically verify dependencies, seed the database if needed, launch the server, and open `http://127.0.0.1:5000` in your web browser.

### Option 2: PowerShell
```powershell
.\start.ps1
```

### Option 3: Command Line (Manual)
1. **Install requirements:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Seed the database (Optional demo data):**
   ```bash
   python backend/seed.py
   ```
3. **Start the server:**
   ```bash
   python backend/app.py
   ```
4. **Open your browser:**
   Navigate to [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 👥 Pre-Configured Demo Accounts

For instant exploration, pre-seeded accounts are ready to use (also available as 1-click quick-login buttons on the landing page):

| User | Username / Email | Password | Role / Vault Contents |
| :--- | :--- | :--- | :--- |
| **Narayanan Ram** | `narayanan` / `narayanan@example.com` | `LoveStory2026!` | Vault owner with 5 memories (first date, sunrise trip, quiet monsoon, road trip video, private letters). Connected with Anu Maria. |
| **Anu Maria** | `anumaria` / `anu@example.com` | `LoveStory2026!` | Connected partner with 3 memories (beach sunset, birthday party, private sketches). |
| **Siddharth** | `sid` / `sid@example.com` | `LoveStory2026!` | Longtime friend with a pending connection request sent to Narayanan. |

---

## 📁 Project Architecture

```
GALLERY/
├── backend/                  # Python Flask Application
│   ├── app.py                # Flask app entrypoint & SPA static router
│   ├── auth.py               # Auth decorators, token serializers, validation
│   ├── config.py             # App configuration & directory management
│   ├── database.py           # SQLite schema definitions & connection pool
│   ├── security.py           # Permissions validator & sanitization helpers
│   ├── seed.py               # Seed script with demo accounts & sample media
│   ├── storage.py            # Media storage, thumbnail generation & streaming
│   └── routes/               # Blueprint API Routes
│       ├── auth_routes.py    # Register, login, reset password, profile
│       ├── connection_routes.py # Connect requests, accept, reject, list
│       ├── media_routes.py   # Secure media & thumbnail streaming
│       ├── memory_routes.py  # CRUD operations for memories & privacy
│       ├── notification_routes.py # In-app notifications
│       ├── shared_routes.py  # Shared memories retrieval
│       └── user_routes.py    # User search & profile update
├── frontend/                 # Single Page Application (SPA)
│   ├── index.html            # Main HTML document
│   ├── css/
│   │   ├── base.css          # Reset, base styles & typography
│   │   ├── components.css    # Buttons, cards, modals, form inputs, toasts
│   │   ├── variables.css     # CSS design tokens (light & dark mode variables)
│   │   └── views.css         # Page layouts, grid systems, timelines
│   └── js/
│       ├── api.js            # REST API client wrapper
│       ├── app.js            # Main bootstrapper & global event listeners
│       ├── auth.js           # Session & user state management
│       ├── router.js         # Hash-based SPA client router
│       └── views.js          # Dynamic DOM rendering engine & modals
├── storage/                  # Local Persistent Storage
│   ├── database.sqlite       # SQLite database file
│   ├── media/                # Full-size photos and videos
│   ├── thumbnails/           # Auto-generated WebP thumbnails
│   └── avatars/              # User profile avatars
├── tests/                    # Automated Test Suite
│   ├── test_auth.py          # Authentication & registration tests
│   ├── test_memories.py      # Memory creation & query tests
│   ├── test_permissions.py   # Access control & privacy tests
│   └── test_system_e2e.py    # Full end-to-end integration tests
├── .env                      # Environment configuration
├── .env.example              # Sample environment template
├── requirements.txt          # Python package dependencies
├── start.bat                 # 1-Click Windows launcher
├── start.ps1                 # PowerShell launcher
└── start.sh                  # Bash / Linux / macOS launcher
```

---

## 🧪 Running Tests

The test suite validates authentication, password validation, upload handling, permission controls, and complete end-to-end user workflows:

```bash
python -m unittest discover tests
```

All 6 test suites execute with isolated in-memory/temporary SQLite databases.

---

## ⚙️ Configuration (.env)

| Variable | Default | Description |
| :--- | :--- | :--- |
| `SECRET_KEY` | `som-super-secret-vault-key-2026-secure` | Secret used for token serialization & hashing |
| `PORT` | `5000` | HTTP port for the web server |
| `HOST` | `0.0.0.0` | Bind host address |
| `DEBUG` | `True` | Flask debug mode |
| `DATABASE_PATH` | `storage/database.sqlite` | SQLite database file location |
| `STORAGE_DIR` | `storage` | Media storage root directory |
| `MAX_CONTENT_LENGTH` | `104857600` | Maximum file upload size (100 MB) |
| `TOKEN_EXPIRE_HOURS` | `72` | Session token lifespan in hours |
