import os
from PIL import Image
from services.smart_layout import find_optimal_crop


def compose_creative(bg_path, panel_path, logo_path, output_path, target_size):
    target_w, target_h = target_size

    # Step 1: Load background and smart crop it to the right size
    bg = Image.open(bg_path).convert("RGB")

    # Find the optimal crop to avoid putting the panel over important content
    crop_x, crop_y, crop_w, crop_h = find_optimal_crop(bg, target_w, target_h)
    cropped = bg.crop((crop_x, crop_y, crop_x + crop_w, crop_y + crop_h))
    canvas = cropped.resize((target_w, target_h), Image.LANCZOS)

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

