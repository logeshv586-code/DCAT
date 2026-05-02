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

The server starts at **http://localhost:8001**

On first run, the database is automatically created and seeded with:
- Admin account
- Brand accounts (Tata, Volkswagen)
- Dealership records mapped to the provided asset folders

### 3. Open the App

Visit **http://localhost:8001** in your browser.

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

## Computer Vision Automation Features

The DCAT project uses a deterministic, computer vision-based automation approach rather than LLMs or cloud AI services. Layout decisions are driven by OpenCV heuristics, scoring functions, and fixed safety constraints so the output remains fast, private, and repeatable.

### AI Feature: Text Overlap Avoidance System
The layout engine includes a computer vision-based heuristic model that reduces the chance of dealership panels covering important background text or busy visual content:
- **Edge Density Risk Scoring:** The system applies OpenCV edge detection and occupancy analysis to estimate how text-heavy or visually dense the reserved panel area is.
- **Candidate Crop Evaluation:** Multiple candidate crops are tested for each output format, including top, center, bottom, and shifted variants depending on the source aspect ratio.
- **Panel Safe-Zone Reservation:** A fixed `SAFE_ZONE` of 25% of the frame is treated as protected layout space for the dealership panel.
- **Heuristic Scoring Function:** The final crop is chosen by minimizing the combined risk score for the protected panel zone and its immediate visual buffer.

### 2. Smart Scaling & Responsive Cropping
Instead of naive stretching, the system uses "intelligent cover-fill" logic. It calculates the optimal crop based on the target aspect ratio (Square, Portrait, or Story) to preserve the most relevant visual information while filling the canvas completely.

### 3. Aspect-Ratio Aware Candidate Search
The crop selector adapts its search strategy to the source image. Taller images are tested with top, center, bottom, and shifted vertical crops, while wider images are tested with left, center, right, and shifted horizontal crops to find the cleanest reserved panel zone.

### 4. Auto Logo Contrast Picker
A brightness-sensing heuristic samples the background region where the logo is placed. It automatically switches between `logo-dark.png` and `logo-light.png` to guarantee maximum readability and brand compliance.

### 5. Deterministic AI Decision-Making
The system simulates AI-style layout decisions using deterministic computer vision heuristics with no external AI dependency. This keeps generation fast, private, and predictable while still providing adaptive crop selection.

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
