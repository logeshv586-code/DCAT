import os

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

# Asset directories from the original project
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets", "assets")
DEALERSHIP_PANELS_DIR = os.path.join(ASSETS_DIR, "Dealership-panels")
LOGOS_DIR = os.path.join(ASSETS_DIR, "Logos")
SAMPLE_IMAGES_DIR = os.path.join(ASSETS_DIR, "Sample-input-images")

# Directories that get created at runtime
UPLOADS_DIR = os.path.join(PROJECT_ROOT, "uploads")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")

# Make sure the runtime dirs exist (create them if not)
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Database stuff
DATABASE_PATH = os.path.join(BASE_DIR, "dcat.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# JWT settings for auth
JWT_SECRET = "dcat-secret-key-change-in-production"  # don't forget to change this!
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 480  # 8 hours should be enough

# Image upload rules
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB max file size

# Output sizes we support (for social media posts)
OUTPUT_FORMATS = {
    "square": (1080, 1080),
    "portrait": (1080, 1350),
    "story": (1080, 1920),
}

# Maps brand slugs to their actual folder names in the assets
BRAND_FOLDERS = {
    "tata": "Tata-dealers",
    "volkswagen": "VW-dealers",
}

