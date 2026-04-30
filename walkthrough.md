# DCAT — Project Walkthrough

The **Dealership Creative Automation Tool (DCAT)** is now fully implemented and verified. It allows marketing teams to generate high-quality, brand-compliant social media creatives in bulk for multiple dealerships with minimal effort.

## Key Features

- **Bulk Creative Generation**: Select multiple dealerships and generate custom creatives for all of them at once.
- **Multiple Output Formats**: Supports Square (1080x1080), Portrait (1080x1350), and Story (1080x1920).
- **Intelligent Layout**: Automatically positions dealership panels and selects logo variants based on background contrast.
- **Secure Access**: JWT-based authentication for the admin dashboard.
- **Fast Processing**: Uses multi-threading for parallel image processing.

## AI & Automation Highlights

| Feature | Description |
|---------|-------------|
| **Smart Scaling** | Uses center-weighted cover cropping to fill the canvas without distortion, favoring the top 60% of the image to keep subjects visible above the footer panel. |
| **Panel Edge Detection** | Scans the dealership panel's alpha channel to find where visible content starts, ensuring the footer bar is perfectly aligned at the bottom. |
| **Text Overlap Avoidance** | Uses OpenCV Canny edge detection to identify text or busy regions in the background; if they clash with the panel zone, the crop is automatically shifted. |
| **Auto Logo Contrast** | Analyzes the background brightness in the logo zone and picks either the `dark` or `light` logo variant to ensure visibility. |

## Verification Results

The system was verified using a dedicated API test suite and manual code review.

### Sample Generated Output
Here are the results of a bulk generation for Volkswagen dealerships:

````carousel
![VW Hubli Creative](file:///D:/DCAT/output/a17b27bf53f74404a8b4ddfda9d19edf.jpg)
<!-- slide -->
![VW Autobahn Creative](file:///D:/DCAT/output/6dd8afe737d547709645257b0e54d2d0.jpg)
````

### Backend Status
The FastAPI server is running on port **8001** and is ready for use.
- **Login**: `admin` / `admin123`
- **Docs**: [http://localhost:8001/docs](http://localhost:8001/docs)

## Project Structure

- `backend/`: FastAPI application, image processing services, and SQLite database.
- `frontend/`: Vanilla HTML/CSS/JS dashboard.
- `assets/`: Provided brand assets (panels, logos).
- `output/`: Directory for generated creatives.
- `uploads/`: Directory for user-uploaded background images.
