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

# thread pool for parallel batch processing
_pool = ThreadPoolExecutor(max_workers=4)


def _save_upload(file: UploadFile) -> str:
    """Save uploaded file to disk, return the filename."""
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    unique_name = f"{uuid.uuid4().hex}{ext}"
    dest = os.path.join(UPLOADS_DIR, unique_name)
    contents = file.file.read()
    with open(dest, "wb") as f:
        f.write(contents)
    return unique_name


def _resolve_panel_dir(dealer: Dealership, brand_slug: str) -> str:
    """Figure out the filesystem path to a dealer's panel folder."""
    brand_folder = BRAND_FOLDERS.get(brand_slug)
    if not brand_folder:
        raise HTTPException(status_code=400, detail=f"Unknown brand slug: {brand_slug}")
    return os.path.join(DEALERSHIP_PANELS_DIR, brand_folder, dealer.folder_name)


def _pick_template(panel_dir: str, fmt: str) -> str:
    """Pick template.png for square, template1.png for portrait/story."""
    if fmt == "square":
        path = os.path.join(panel_dir, "template.png")
    else:
        path = os.path.join(panel_dir, "template1.png")

    # fallback: if the preferred one doesn't exist, use the other
    if not os.path.exists(path):
        alt = os.path.join(panel_dir, "template1.png" if fmt == "square" else "template.png")
        if os.path.exists(alt):
            return alt
        raise HTTPException(status_code=500, detail=f"No panel template found in {panel_dir}")
    return path


@router.post("/generate")
def generate_creatives(
    background: UploadFile = File(...),
    dealer_ids: str = Form(...),         # comma-separated ids
    output_format: str = Form("square"), # square | portrait | story
    logo_enabled: str = Form("off"),     # off | dark | light
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # validate format
    if output_format not in OUTPUT_FORMATS:
        raise HTTPException(status_code=400, detail=f"Invalid format. Choose from: {list(OUTPUT_FORMATS.keys())}")

    target_w, target_h = OUTPUT_FORMATS[output_format]

    # parse dealer ids
    try:
        ids = [int(x.strip()) for x in dealer_ids.split(",") if x.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="dealer_ids must be comma-separated integers")

    if not ids:
        raise HTTPException(status_code=400, detail="Select at least one dealership")

    # save the background image
    bg_filename = _save_upload(background)
    bg_path = os.path.join(UPLOADS_DIR, bg_filename)

    # fetch dealers from db
    dealers = db.query(Dealership).filter(Dealership.id.in_(ids)).all()
    if not dealers:
        raise HTTPException(status_code=404, detail="No matching dealerships found")

    # we need the brand slug for each dealer to find the right panel folder
    account_cache = {}
    results = []

    def _process_one_dealer(dealer):
        """Process a single dealer — runs in thread pool."""
        if dealer.account_id not in account_cache:
            acct = db.query(Account).get(dealer.account_id)
            account_cache[dealer.account_id] = acct.slug if acct else "unknown"
        brand_slug = account_cache[dealer.account_id]

        panel_dir = _resolve_panel_dir(dealer, brand_slug)
        template_path = _pick_template(panel_dir, output_format)

        # figure out logo path if needed
        logo_path = None
        if logo_enabled in ("dark", "light"):
            logo_file = f"logo-{logo_enabled}.png"
            candidate = os.path.join(panel_dir, logo_file)
            if os.path.exists(candidate):
                logo_path = candidate

        # generate output filename
        out_name = f"{uuid.uuid4().hex}.jpg"
        out_path = os.path.join(OUTPUT_DIR, out_name)

        # do the actual compositing
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

    # batch process — use thread pool for parallelism
    if len(dealers) == 1:
        # no need for threading overhead on a single item
        info = _process_one_dealer(dealers[0])
        results.append(info)
    else:
        futures = {_pool.submit(_process_one_dealer, d): d for d in dealers}
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

    # save records to db
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
    """Package multiple generated images into a single ZIP."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, fname in enumerate(filenames):
            path = os.path.join(OUTPUT_DIR, fname)
            if os.path.exists(path):
                # give them nicer names in the zip
                arcname = f"creative_{i+1}.jpg"
                zf.write(path, arcname)

    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=creatives.zip"},
    )
