import os
from PIL import Image
from services.smart_layout import find_optimal_crop, find_panel_content_top


def compose_creative(bg_path, panel_path, logo_path, output_path, target_size):
    target_w, target_h = target_size

    # Step 1: Load background
    bg = Image.open(bg_path).convert("RGB")

    # Step 2: Load and prepare the dealership panel
    # We do this first so we can find the exact boundary for the car image
    panel = Image.open(panel_path).convert("RGBA")
    panel_aspect = panel.height / panel.width
    new_panel_h = int(target_w * panel_aspect)
    panel_resized = panel.resize((target_w, new_panel_h), Image.LANCZOS)

    panel_x = 0
    panel_y = target_h - new_panel_h

    # Find where the actual content (text) starts in the panel
    # This allows us to remove the "transparent" blurred gap between the car and the panel
    panel_content_y_offset = find_panel_content_top(panel_resized)
    content_h = panel_y + panel_content_y_offset

    # Step 3: Create the background and car layer
    from PIL import ImageFilter
    full_crop_x, full_crop_y, full_crop_w, full_crop_h = find_optimal_crop(bg, target_w, target_h)
    full_cropped = bg.crop((full_crop_x, full_crop_y, full_crop_x + full_crop_w, full_crop_y + full_crop_h))
    canvas = full_cropped.resize((target_w, target_h), Image.LANCZOS).filter(ImageFilter.GaussianBlur(25))

    # Find the optimal crop for the car image area (meeting the panel boundary exactly)
    crop_x, crop_y, crop_w, crop_h = find_optimal_crop(bg, target_w, content_h)
    content_cropped = bg.crop((crop_x, crop_y, crop_x + crop_w, crop_y + crop_h))
    
    # Resize the car image to fill the FULL width and the exact height above the panel
    content_layer = content_cropped.resize((target_w, content_h), Image.LANCZOS)

    # Paste the car image onto the canvas
    canvas.paste(content_layer, (0, 0))

    # Add a solid white rectangle behind the dealership info
    from PIL import ImageDraw
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([0, content_h, target_w, target_h], fill="white")

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

