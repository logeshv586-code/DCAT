# DCAT — Dealership Creative Automation Tool

A web-based tool that automates generation of dealership marketing creatives. Upload a background image, choose a brand and dealership(s), and the tool composites everything together — panel overlay, logo placement — in bulk, across multiple output formats.

## Tech Stack

- **Backend:** Python 3.12+, FastAPI, SQLAlchemy, SQLite
- **Frontend:** Vanilla HTML / CSS / JavaScript (no frameworks)
- **Image Processing:** Pillow (PIL), OpenCV (for edge detection)
- **Auth:** JWT (python-jose)

## Setup Instructions

### 1. Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Run the Server

```bash
cd backend
python main.py
```

The server starts at **http://localhost:8000**

On first run, the database is automatically created and seeded with:
- Admin account
- Brand accounts (Tata, Volkswagen)
- Dealership records mapped to the provided asset folders

### 3. Open the App

Visit **http://localhost:8000** in your browser.

### Default Admin Credentials

| Username | Password |
|----------|----------|
| `admin`  | `admin123` |

## How to Use

1. **Login** with the admin credentials
2. **Select a brand** (Tata or Volkswagen) from the dropdown
3. **Pick dealership(s)** — check one or multiple for bulk generation
4. **Toggle logo** — enable to overlay the dealer logo (dark/light variant)
5. **Upload a background image** — drag-and-drop or click to browse (JPG/PNG)
6. **Choose output format:**
   - Square: 1080 × 1080 (Instagram post)
   - Portrait: 1080 × 1350 (Instagram post)
   - Story: 1080 × 1920 (Instagram story)
7. **Click Generate** — creatives are produced for each selected dealership
8. **Preview & Download** — click any thumbnail to preview full-size; download individually or all at once as a ZIP

## Database

SQLite is used for simplicity — no external database server needed. The schema dump file is at `backend/database.sql` and can be loaded manually:

```bash
sqlite3 backend/dcat.db < backend/database.sql
```

However, the app auto-creates and seeds the database on first launch, so manual setup is optional.

## Project Structure

```
DCAT/
├── backend/
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Settings and paths
│   ├── database.py          # DB engine, session, seeding
│   ├── models.py            # ORM models
│   ├── auth.py              # Password hashing, JWT helpers
│   ├── database.sql         # Schema + seed data dump
│   ├── requirements.txt
│   ├── routers/
│   │   ├── auth_router.py
│   │   ├── accounts_router.py
│   │   ├── dealers_router.py
│   │   └── generate_router.py
│   └── services/
│       ├── compositor.py    # Image compositing pipeline
│       └── smart_layout.py  # AI/automation logic
├── frontend/
│   ├── index.html           # Login page
│   ├── dashboard.html       # Main tool UI
│   ├── css/styles.css
│   └── js/
│       ├── login.js
│       └── dashboard.js
├── assets/                  # Provided dealership panels, logos, sample images
├── uploads/                 # User-uploaded backgrounds (created at runtime)
├── output/                  # Generated creatives (created at runtime)
└── README.md
```

## AI / Automation Features

The assignment requires at least one intelligent automation. This project implements several:

### 1. Smart Scaling (Cover Crop)
Instead of naively stretching or letterboxing, the system calculates a center-weighted crop that fills the target canvas completely — no whitespace, no distortion. The vertical bias is 40/60 (favoring the top of the image) because the bottom is where the dealership panel goes.

### 2. Panel Edge Detection
The dealership panel PNGs have large transparent areas at the top. The system scans the alpha channel to detect where the actual visible content begins, ensuring precise alignment at the bottom of the canvas.

### 3. Text Overlap Avoidance
Using OpenCV's Canny edge detector, the system analyzes the background region where the panel will be placed. If it detects high edge density (indicating text or busy detail), it adjusts the crop offset to minimize visual conflict between the background and the overlay.

### 4. Auto Logo Contrast Selection
When logo is enabled, the system samples the average brightness of the background area where the logo will be placed, then automatically selects the dark or light logo variant for maximum readability.

### 5. Batch Parallel Processing
When generating creatives for multiple dealerships, the system uses Python's ThreadPoolExecutor for concurrent processing, significantly reducing wait times for bulk jobs.

## Assumptions

- The provided asset folder structure is maintained (brand folders → dealer folders → template.png / template1.png / logos)
- `template.png` is used for square output, `template1.png` for portrait/story formats
- Each dealer folder contains `logo-dark.png` and `logo-light.png`
- The dealership panel PNGs have transparency (RGBA) — the visible content (footer bar) is at the bottom
- Output is always saved as JPEG at 95% quality
- Single background image per generation batch (same background applied to all selected dealers)

## Dependencies

See `backend/requirements.txt`. Key packages:

| Package | Purpose |
|---------|---------|
| fastapi | Web framework |
| uvicorn | ASGI server |
| SQLAlchemy | ORM for SQLite |
| Pillow | Image compositing |
| opencv-python-headless | Edge detection for text overlap |
| python-jose | JWT token handling |
| python-multipart | File upload parsing |