"""
compositor.py
The main image compositing pipeline. Takes a background image, a dealership
panel (transparent PNG), and optionally a logo, then combines them into
a final creative at the specified target size.
"""

import os
from PIL import Image
from services.smart_layout import (
    smart_crop_offsets,
    find_panel_content_top,
    suggest_crop_adjustment,
)


def compose_creative(bg_path, panel_path, logo_path, output_path, target_size):
    """
    Main compositing function.

    bg_path:     path to the uploaded background image
    panel_path:  path to the dealership panel PNG (with transparency)
    logo_path:   path to the logo PNG, or None if logo disabled
    output_path: where to save the final image
    target_size: (width, height) tuple, e.g. (1080, 1080)
    """
    target_w, target_h = target_size

    # --- step 1: load and smart-crop the background ---
    bg = Image.open(bg_path).convert("RGB")
    orig_w, orig_h = bg.size

    # get base crop coordinates
    crop_x, crop_y, crop_w, crop_h = smart_crop_offsets(orig_w, orig_h, target_w, target_h)

    # check if the panel zone has text overlap, adjust if needed
    shift = suggest_crop_adjustment(bg, target_w, target_h)
    if shift > 0:
        # shift crop down to avoid text under the panel
        max_y = orig_h - crop_h
        crop_y = min(crop_y + shift, max_y)

    # do the crop
    cropped = bg.crop((crop_x, crop_y, crop_x + crop_w, crop_y + crop_h))

    # resize to exact target dimensions (high quality)
    canvas = cropped.resize((target_w, target_h), Image.LANCZOS)

    # --- step 2: overlay the dealership panel ---
    panel = Image.open(panel_path).convert("RGBA")

    # find where the actual content starts in the panel
    content_top = find_panel_content_top(panel)

    # scale panel to match canvas width
    panel_aspect = panel.height / panel.width
    new_panel_w = target_w
    new_panel_h = int(target_w * panel_aspect)
    panel_resized = panel.resize((new_panel_w, new_panel_h), Image.LANCZOS)

    # position panel at the bottom of the canvas
    panel_x = 0
    panel_y = target_h - new_panel_h

    # paste with transparency
    canvas_rgba = canvas.convert("RGBA")
    canvas_rgba.paste(panel_resized, (panel_x, panel_y), panel_resized)

    # --- step 3: overlay logo if enabled ---
    if logo_path and os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")

        # scale logo — aim for about 8% of canvas width
        logo_target_w = int(target_w * 0.08)
        logo_scale = logo_target_w / logo.width
        logo_target_h = int(logo.height * logo_scale)
        logo_resized = logo.resize((logo_target_w, logo_target_h), Image.LANCZOS)

        # place in top-left corner with some padding
        pad = int(target_w * 0.03)
        canvas_rgba.paste(logo_resized, (pad, pad), logo_resized)

    # --- step 4: save final output ---
    final = canvas_rgba.convert("RGB")
    final.save(output_path, "JPEG", quality=95)
