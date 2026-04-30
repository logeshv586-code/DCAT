import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

# where the provided assets live
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets", "assets")
DEALERSHIP_PANELS_DIR = os.path.join(ASSETS_DIR, "Dealership-panels")
LOGOS_DIR = os.path.join(ASSETS_DIR, "Logos")
SAMPLE_IMAGES_DIR = os.path.join(ASSETS_DIR, "Sample-input-images")

# runtime directories
UPLOADS_DIR = os.path.join(PROJECT_ROOT, "uploads")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")

# make sure they exist
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# db
DATABASE_PATH = os.path.join(BASE_DIR, "dcat.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# jwt
JWT_SECRET = "dcat-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 480  # 8 hours

# image stuff
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB

# output format presets
OUTPUT_FORMATS = {
    "square": (1080, 1080),
    "portrait": (1080, 1350),
    "story": (1080, 1920),
}

# brand-to-folder mapping
BRAND_FOLDERS = {
    "tata": "Tata-dealers",
    "volkswagen": "VW-dealers",
}
