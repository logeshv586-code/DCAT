import numpy as np
from PIL import Image

# Try to import OpenCV for edge detection - if not, we'll use a simple fallback
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

# Some constants for the layout logic
SAFE_ZONE = 0.25       # Reserve bottom 25% for the panel
BUFFER_ZONE = 0.10     # Extra buffer area above the panel
RISK_THRESHOLD = 0.15  # If score is above this, area is too busy
VERY_LOW_RISK_THRESHOLD = 0.02


# Calculate how "risky" a region is for placing the panel (i.e., how busy it is)
def calculate_text_risk(region_gray):
    if region_gray.size == 0:
        return float("inf")

    if not HAS_CV2:
        # Fallback: just use standard deviation of pixel values as a rough measure
        return float(np.std(region_gray)) / 255.0

    # Blur the image first to reduce noise
    blurred = cv2.GaussianBlur(region_gray, (5, 5), 0)
    # Find edges with Canny
    edges = cv2.Canny(blurred, 50, 150)

    # Calculate edge density
    edge_mask = edges > 0
    edge_density = float(np.count_nonzero(edge_mask)) / float(edge_mask.size)

    # Dilate edges to fill small gaps, then calculate occupancy
    kernel = np.ones((3, 3), np.uint8)
    dilated = cv2.dilate(edges, kernel, iterations=1)
    occupancy = float(np.count_nonzero(dilated)) / float(dilated.size)

    # Check for horizontal lines (which might indicate text)
    row_density = edge_mask.mean(axis=1)
    line_threshold = max(edge_density * 1.5, 0.02)
    active_rows = row_density > line_threshold
    line_activity = float(np.count_nonzero(active_rows)) / float(len(active_rows))

    # Combine all scores into one total risk value
    return (edge_density * 0.5) + (occupancy * 0.3) + (line_activity * 0.2)


# Calculate a crop box with a given bias (0 = start, 0.5 = center, 1 = end)
def get_crop_region(
    img_w,
    img_h,
    target_w,
    target_h,
    vertical_bias=0.5,
    horizontal_bias=0.5,
):
    src_ratio = img_w / img_h
    tgt_ratio = target_w / target_h

    if src_ratio > tgt_ratio:
        # Image is wider than target, so crop horizontally
        crop_h = img_h
        crop_w = int(round(img_h * tgt_ratio))
        crop_y = 0
        max_offset = max(img_w - crop_w, 0)
        crop_x = int(round(max_offset * horizontal_bias))
    else:
        # Image is taller than target, so crop vertically
        crop_w = img_w
        crop_h = int(round(img_w / tgt_ratio))
        crop_x = 0
        max_offset = max(img_h - crop_h, 0)
        crop_y = int(round(max_offset * vertical_bias))

    return crop_x, crop_y, crop_w, crop_h


# Score a specific crop candidate
def _score_crop(gray_full, crop_box, safe_zone=SAFE_ZONE):
    crop_x, crop_y, crop_w, crop_h = crop_box

    # How much of the bottom is the panel going to take?
    panel_zone_h = max(1, int(round(crop_h * safe_zone)))
    buffer_zone_h = max(panel_zone_h, int(round(crop_h * (safe_zone + BUFFER_ZONE))))

    panel_top = crop_y + crop_h - panel_zone_h
    buffer_top = crop_y + crop_h - buffer_zone_h

    # Extract the regions we care about
    panel_region = gray_full[panel_top : crop_y + crop_h, crop_x : crop_x + crop_w]
    buffer_region = gray_full[buffer_top : crop_y + crop_h, crop_x : crop_x + crop_w]

    # Calculate risk scores
    panel_risk = calculate_text_risk(panel_region)
    buffer_risk = calculate_text_risk(buffer_region)
    total_risk = (panel_risk * 0.8) + (buffer_risk * 0.2)

    return total_risk, panel_risk, buffer_risk


# Find the best crop that minimizes risk in the panel area
def find_optimal_crop(bg_img, target_w, target_h):
    img_w, img_h = bg_img.size
    gray_full = np.array(bg_img.convert("L"))
    src_ratio = img_w / img_h
    tgt_ratio = target_w / target_h
    
    # Adjust SAFE_ZONE based on format
    # For Story (1080x1920), panel is proportionally taller, increase SAFE_ZONE to 0.30
    current_safe_zone = 0.30 if target_h / target_w > 1.5 else SAFE_ZONE

    # Different positions to try based on image aspect ratio
    if src_ratio > tgt_ratio:
        positions = [
            {"name": "left", "vertical_bias": 0.5, "horizontal_bias": 0.0},
            {"name": "left_shifted_1", "vertical_bias": 0.5, "horizontal_bias": 0.1},
            {"name": "left_shifted_2", "vertical_bias": 0.5, "horizontal_bias": 0.2},
            {"name": "left_shifted_3", "vertical_bias": 0.5, "horizontal_bias": 0.3},
            {"name": "center_left", "vertical_bias": 0.5, "horizontal_bias": 0.4},
            {"name": "center", "vertical_bias": 0.5, "horizontal_bias": 0.5},
            {"name": "center_right", "vertical_bias": 0.5, "horizontal_bias": 0.6},
            {"name": "right_shifted_3", "vertical_bias": 0.5, "horizontal_bias": 0.7},
            {"name": "right_shifted_2", "vertical_bias": 0.5, "horizontal_bias": 0.8},
            {"name": "right_shifted_1", "vertical_bias": 0.5, "horizontal_bias": 0.9},
            {"name": "right", "vertical_bias": 0.5, "horizontal_bias": 1.0},
        ]
    else:
        positions = [
            {"name": "top", "vertical_bias": 0.0, "horizontal_bias": 0.5},
            {"name": "top_shifted_1", "vertical_bias": 0.1, "horizontal_bias": 0.5},
            {"name": "top_shifted_2", "vertical_bias": 0.2, "horizontal_bias": 0.5},
            {"name": "top_shifted_3", "vertical_bias": 0.3, "horizontal_bias": 0.5},
            {"name": "center_top", "vertical_bias": 0.4, "horizontal_bias": 0.5},
            {"name": "center", "vertical_bias": 0.5, "horizontal_bias": 0.5},
            {"name": "center_bottom", "vertical_bias": 0.6, "horizontal_bias": 0.5},
            {"name": "bottom_shifted_3", "vertical_bias": 0.7, "horizontal_bias": 0.5},
            {"name": "bottom_shifted_2", "vertical_bias": 0.8, "horizontal_bias": 0.5},
            {"name": "bottom_shifted_1", "vertical_bias": 0.9, "horizontal_bias": 0.5},
            {"name": "bottom", "vertical_bias": 1.0, "horizontal_bias": 0.5},
        ]

    best_crop = None
    best_score = float("inf")
    seen_crops = set()

    # Evaluate all candidate crops
    for pos in positions:
        crop_box = get_crop_region(
            img_w,
            img_h,
            target_w,
            target_h,
            vertical_bias=pos["vertical_bias"],
            horizontal_bias=pos["horizontal_bias"],
        )

        if crop_box in seen_crops:
            continue

        seen_crops.add(crop_box)
        total_risk, panel_risk, buffer_risk = _score_crop(gray_full, crop_box, current_safe_zone)
        print(
            f"Evaluated {pos['name']} crop: total={total_risk:.4f}, "
            f"panel={panel_risk:.4f}, buffer={buffer_risk:.4f}"
        )

        if total_risk < best_score:
            best_score = total_risk
            best_crop = crop_box

        # If we find a really low-risk crop, we can just stop early
        if total_risk <= VERY_LOW_RISK_THRESHOLD:
            break

    # Fallback to center crop if nothing else worked
    if best_crop is None:
        best_crop = get_crop_region(img_w, img_h, target_w, target_h)
        best_score, _, _ = _score_crop(gray_full, best_crop, current_safe_zone)

    if best_score > RISK_THRESHOLD:
        print(
            f"Warning: No low-risk crop found. Using safest one with score {best_score:.4f}"
        )

    return best_crop


# Find where the actual panel content starts (from the top of the image)
def find_panel_content_top(panel_img):
    if panel_img.mode != "RGBA":
        return 0

    alpha = np.array(panel_img.split()[3])
    h = alpha.shape[0]

    threshold = alpha.shape[1] * 0.05
    for y in range(h):
        if np.sum(alpha[y] > 30) > threshold:
            return y

    return 0


# Automatically pick dark or light logo based on background brightness
def pick_logo_variant(bg_img, logo_x, logo_y, logo_w, logo_h):
    region = bg_img.crop((logo_x, logo_y, logo_x + logo_w, logo_y + logo_h))
    grayscale = region.convert("L")
    avg_brightness = np.mean(np.array(grayscale))

    if avg_brightness < 128:
        return "light"  # Dark background, use light logo
    return "dark"  # Bright background, use dark logo

