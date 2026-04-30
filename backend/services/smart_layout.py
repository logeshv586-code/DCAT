"""
smart_layout.py
Handles the "AI / Automation" parts of the creative generation:
  - smart crop (center-weighted cover fill)
  - panel edge detection (find where actual content starts in the panel PNG)
  - logo contrast picker (dark vs light)
  - text overlap check using edge density
"""

import numpy as np
from PIL import Image

# try to import cv2 for edge detection; fall back gracefully
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False


def smart_crop_offsets(img_w, img_h, target_w, target_h):
    """
    Calculate how to crop the image to fill the target canvas
    without distortion or whitespace.

    Returns (crop_x, crop_y, crop_w, crop_h) — the region to extract
    from the original image.

    Strategy: scale to cover, then center-crop. We bias the vertical
    crop slightly toward the top (60/40 split) because the bottom
    of the image is where the dealership panel will go, and we'd rather
    preserve the top content.
    """
    src_ratio = img_w / img_h
    tgt_ratio = target_w / target_h

    if src_ratio > tgt_ratio:
        # image is wider than target — crop sides
        crop_h = img_h
        crop_w = int(img_h * tgt_ratio)
        crop_y = 0
        crop_x = (img_w - crop_w) // 2  # center horizontally
    else:
        # image is taller than target — crop top/bottom
        crop_w = img_w
        crop_h = int(img_w / tgt_ratio)
        crop_x = 0
        # bias toward top: 40% from top, 60% from bottom
        max_offset = img_h - crop_h
        crop_y = int(max_offset * 0.4)

    return crop_x, crop_y, crop_w, crop_h


def find_panel_content_top(panel_img):
    """
    Given a panel image (RGBA), scan from the top to find the first row
    where there's significant opaque content. This tells us how much
    of the panel is actually "empty" at the top, so we know where the
    real footer content starts.

    Returns the Y coordinate (from top) where content begins.
    """
    if panel_img.mode != "RGBA":
        # if there's no alpha, assume content fills the whole thing
        return 0

    alpha = np.array(panel_img.split()[3])  # alpha channel
    h = alpha.shape[0]

    # scan top-down; look for a row where > 5% of pixels are opaque
    threshold = alpha.shape[1] * 0.05
    for y in range(h):
        if np.sum(alpha[y] > 30) > threshold:
            return y

    return 0  # whole thing is empty? shouldn't happen


def pick_logo_variant(bg_img, logo_x, logo_y, logo_w, logo_h):
    """
    Look at the background region where the logo will be placed.
    Calculate average brightness. If it's dark, use the light logo;
    if it's light, use the dark logo.

    Returns "dark" or "light".
    """
    region = bg_img.crop((logo_x, logo_y, logo_x + logo_w, logo_y + logo_h))
    grayscale = region.convert("L")
    avg_brightness = np.mean(np.array(grayscale))

    # below 128 = dark background → use light logo
    if avg_brightness < 128:
        return "light"
    else:
        return "dark"


def check_text_overlap(bg_img, region_box):
    """
    Uses edge detection to estimate if there's text or busy content
    in the specified region of the background. High edge density
    usually means text, fine details, or patterns that would clash
    with the dealership panel overlay.

    region_box: (left, top, right, bottom)

    Returns a float 0-1 indicating "busyness" of that region.
    0 = very clean, 1 = extremely busy.
    """
    if not HAS_CV2:
        return 0.0  # can't check without opencv

    region = bg_img.crop(region_box)
    gray = np.array(region.convert("L"))

    # canny edge detection
    edges = cv2.Canny(gray, 50, 150)

    # what fraction of pixels are edges?
    density = np.sum(edges > 0) / edges.size
    return min(density * 3.0, 1.0)  # scale up a bit, cap at 1


def suggest_crop_adjustment(bg_img, target_w, target_h, panel_height_ratio=0.15):
    """
    If the panel overlap zone has too much text/edges, suggest shifting
    the crop offset to move the busy region away from the bottom.

    Returns an integer offset adjustment (positive = shift crop down more).
    """
    img_w, img_h = bg_img.size
    crop_x, crop_y, crop_w, crop_h = smart_crop_offsets(img_w, img_h, target_w, target_h)

    # the panel will cover roughly the bottom 15% of the output
    panel_zone_h = int(crop_h * panel_height_ratio)
    panel_zone_box = (crop_x, crop_y + crop_h - panel_zone_h, crop_x + crop_w, crop_y + crop_h)

    # clamp to image bounds
    panel_zone_box = (
        max(0, panel_zone_box[0]),
        max(0, panel_zone_box[1]),
        min(img_w, panel_zone_box[2]),
        min(img_h, panel_zone_box[3]),
    )

    busyness = check_text_overlap(bg_img, panel_zone_box)

    if busyness > 0.3:
        # try shifting the crop up a bit so the busy part moves above the panel zone
        max_shift = img_h - crop_h - crop_y
        shift = min(int(panel_zone_h * 0.5), max_shift)
        return shift

    return 0
