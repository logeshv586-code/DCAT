import os
from PIL import Image
from services.smart_layout import find_optimal_crop


def compose_creative(bg_path, panel_path, logo_path, output_path, target_size):
    target_w, target_h = target_size

    # The panel takes up a specific safe zone at the bottom
    # We will reserve this space so the main image fits exactly ABOVE it
    safe_zone_ratio = 0.30 if target_h / target_w > 1.5 else 0.25
    safe_zone_h = int(target_h * safe_zone_ratio)
    content_h = target_h - safe_zone_h

    # Step 1: Load background
    bg = Image.open(bg_path).convert("RGB")

    # Create a blurred base canvas that fills the entire target size
    from PIL import ImageFilter
    full_crop_x, full_crop_y, full_crop_w, full_crop_h = find_optimal_crop(bg, target_w, target_h)
    full_cropped = bg.crop((full_crop_x, full_crop_y, full_crop_x + full_crop_w, full_crop_y + full_crop_h))
    canvas = full_cropped.resize((target_w, target_h), Image.LANCZOS).filter(ImageFilter.GaussianBlur(25))

    # Now, find the optimal crop for the top "content" area, so the subject shrinks to fit above the panel
    crop_x, crop_y, crop_w, crop_h = find_optimal_crop(bg, target_w, content_h)
    content_cropped = bg.crop((crop_x, crop_y, crop_x + crop_w, crop_y + crop_h))
    content_layer = content_cropped.resize((target_w, content_h), Image.LANCZOS)

    # Paste the sharp, smaller image onto the top portion of the blurred canvas
    canvas.paste(content_layer, (0, 0))

    # Step 2: Overlay the dealership panel
    panel = Image.open(panel_path).convert("RGBA")

    # Scale the panel to fit the full width of the canvas
    panel_aspect = panel.height / panel.width
    new_panel_w = target_w
    new_panel_h = int(target_w * panel_aspect)
    panel_resized = panel.resize((new_panel_w, new_panel_h), Image.LANCZOS)

    # Position the panel at the bottom of the canvas
    panel_x = 0
    panel_y = target_h - new_panel_h

    # Paste the panel with transparency
    canvas_rgba = canvas.convert("RGBA")
    canvas_rgba.paste(panel_resized, (panel_x, panel_y), panel_resized)

    # Step 3: Overlay the logo if it's enabled
    if logo_path and os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")

        # Scale the logo to about 8% of the canvas width
        logo_target_w = int(target_w * 0.08)
        logo_scale = logo_target_w / logo.width
        logo_target_h = int(logo.height * logo_scale)
        logo_resized = logo.resize((logo_target_w, logo_target_h), Image.LANCZOS)

        # Place the logo in the top-left corner with some padding
        pad = int(target_w * 0.03)
        canvas_rgba.paste(logo_resized, (pad, pad), logo_resized)

    # Step 4: Save the final image as JPEG
    final = canvas_rgba.convert("RGB")
    final.save(output_path, "JPEG", quality=95)

