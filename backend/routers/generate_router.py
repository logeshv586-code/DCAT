import os
import uuid
import zipfile
import io
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from concurrent.futures import ThreadPoolExecutor, as_completed

from database import get_db
from models import Dealership, Account, GeneratedCreative
from auth import get_current_user
from config import (
    UPLOADS_DIR, OUTPUT_DIR, ALLOWED_EXTENSIONS,
    OUTPUT_FORMATS, DEALERSHIP_PANELS_DIR, BRAND_FOLDERS,
)
from services.compositor import compose_creative

router = APIRouter(prefix="/api", tags=["generate"])

# Thread pool for parallel processing when generating multiple creatives
_pool = ThreadPoolExecutor(max_workers=4)


# Helper function to save an uploaded image to disk
def _save_upload(file: UploadFile) -> str:
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    unique_name = f"{uuid.uuid4().hex}{ext}"
    dest = os.path.join(UPLOADS_DIR, unique_name)
    contents = file.file.read()
    with open(dest, "wb") as f:
        f.write(contents)
    return unique_name


# Figure out the full path to a dealer's panel folder
def _resolve_panel_dir(dealer: Dealership, brand_slug: str) -> str:
    brand_folder = BRAND_FOLDERS.get(brand_slug)
    if not brand_folder:
        raise HTTPException(status_code=400, detail=f"Unknown brand slug: {brand_slug}")
    return os.path.join(DEALERSHIP_PANELS_DIR, brand_folder, dealer.folder_name)


# Pick which template PNG to use based on output format
def _pick_template(panel_dir: str, fmt: str) -> str:
    # Use template.png for square, template1.png for portrait/story
    if fmt == "square":
        path = os.path.join(panel_dir, "template.png")
    else:
        path = os.path.join(panel_dir, "template1.png")

    # If the preferred template doesn't exist, try the other one
    if not os.path.exists(path):
        alt_path = os.path.join(panel_dir, "template1.png" if fmt == "square" else "template.png")
        if os.path.exists(alt_path):
            return alt_path
        raise HTTPException(status_code=500, detail=f"No panel template found in {panel_dir}")
    return path


@router.post("/generate")
def generate_creatives(
    background: UploadFile = File(...),
    dealer_ids: str = Form(...),         # Comma separated list of dealer IDs
    output_format: str = Form("square"), # Output format: square, portrait, story
    logo_enabled: str = Form("off"),     # Whether to use logo and which variant (dark/light)
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # Validate that the output format is valid
    if output_format not in OUTPUT_FORMATS:
        raise HTTPException(status_code=400, detail=f"Invalid format. Choose from: {list(OUTPUT_FORMATS.keys())}")

    target_w, target_h = OUTPUT_FORMATS[output_format]

    # Parse the comma-separated dealer IDs
    try:
        ids = [int(x.strip()) for x in dealer_ids.split(",") if x.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="dealer_ids must be comma-separated integers")

    if not ids:
        raise HTTPException(status_code=400, detail="Select at least one dealership")

    # Save the uploaded background image
    bg_filename = _save_upload(background)
    bg_path = os.path.join(UPLOADS_DIR, bg_filename)

    # Fetch the selected dealerships from the DB
    dealers = db.query(Dealership).filter(Dealership.id.in_(ids)).all()
    if not dealers:
        raise HTTPException(status_code=404, detail="No matching dealerships found")

    # Cache for account slugs so we don't hit the DB multiple times for the same account
    account_cache = {}
    results = []

    # This function processes a single dealership (runs in thread pool)
    def process_dealer(dealer):
        if dealer.account_id not in account_cache:
            acct = db.query(Account).get(dealer.account_id)
            account_cache[dealer.account_id] = acct.slug if acct else "unknown"
        brand_slug = account_cache[dealer.account_id]

        panel_dir = _resolve_panel_dir(dealer, brand_slug)
        template_path = _pick_template(panel_dir, output_format)

        # Figure out logo path if needed
        logo_path = None
        if logo_enabled in ("dark", "light"):
            logo_file = f"logo-{logo_enabled}.png"
            candidate = os.path.join(panel_dir, logo_file)
            if os.path.exists(candidate):
                logo_path = candidate

        # Generate a unique filename for the output
        out_name = f"{uuid.uuid4().hex}.jpg"
        out_path = os.path.join(OUTPUT_DIR, out_name)

        # Run the actual image compositing
        compose_creative(
            bg_path=bg_path,
            panel_path=template_path,
            logo_path=logo_path,
            output_path=out_path,
            target_size=(target_w, target_h),
        )

        return {
            "dealer_id": dealer.id,
            "dealer_name": dealer.name,
            "output_filename": out_name,
        }

    # Process all selected dealerships
    if len(dealers) == 1:
        # For just one dealer, no need for thread overhead
        info = process_dealer(dealers[0])
        results.append(info)
    else:
        # For multiple dealers, use the thread pool
        futures = {_pool.submit(process_dealer, d): d for d in dealers}
        for future in as_completed(futures):
            try:
                info = future.result()
                results.append(info)
            except Exception as exc:
                dealer = futures[future]
                results.append({
                    "dealer_id": dealer.id,
                    "dealer_name": dealer.name,
                    "error": str(exc),
                })

    # Save all successful generations to the database
    for r in results:
        if "error" not in r:
            record = GeneratedCreative(
                user_id=user["user_id"],
                dealership_id=r["dealer_id"],
                bg_filename=bg_filename,
                output_filename=r["output_filename"],
                format_label=output_format,
            )
            db.add(record)
    db.commit()

    return {
        "count": len([r for r in results if "error" not in r]),
        "format": output_format,
        "results": results,
    }


@router.get("/download/{filename}")
def download_file(filename: str):
    path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, media_type="image/jpeg", filename=filename)


@router.post("/download-zip")
def download_zip(filenames: list[str]):
    # Create a zip file in memory with all the selected images
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, fname in enumerate(filenames):
            path = os.path.join(OUTPUT_DIR, fname)
            if os.path.exists(path):
                # Give the files nicer names in the zip
                arcname = f"creative_{i+1}.jpg"
                zf.write(path, arcname)

    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=creatives.zip"},
    )

