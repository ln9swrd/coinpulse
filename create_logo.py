#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CoinPulse Logo Generator
Combines trans_bg.png logo with "코인펄스" text
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_combined_logo():
    # Load the logo image
    logo_img = Image.open('logo_files/trans_bg.png')

    # Get logo dimensions
    logo_width, logo_height = logo_img.size

    # Create new image with extra width for text
    # Logo on left, text on right
    text_width = int(logo_width * 0.8)  # Space for text
    margin = int(logo_width * 0.1)  # Margin between logo and text

    new_width = logo_width + margin + text_width
    new_height = logo_height

    # Create transparent background
    combined = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 0))

    # Paste logo on the left
    combined.paste(logo_img, (0, 0), logo_img)

    # Prepare to draw text
    draw = ImageDraw.Draw(combined)

    # Try to load Korean font
    font_size = int(logo_height * 0.35)
    font_paths = [
        'C:/Windows/Fonts/malgun.ttf',  # Malgun Gothic (Windows)
        'C:/Windows/Fonts/gulim.ttc',   # Gulim (Windows)
        'C:/Windows/Fonts/NanumGothic.ttf',  # Nanum Gothic
        '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',  # Linux
    ]

    font = None
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                font = ImageFont.truetype(font_path, font_size)
                print(f"Loaded font: {font_path}")
                break
            except Exception as e:
                print(f"Failed to load {font_path}: {e}")
                continue

    if font is None:
        print("Using default font (may not display Korean properly)")
        font = ImageFont.load_default()

    # Text to draw
    text = "코인펄스"

    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width_actual = bbox[2] - bbox[0]
    text_height_actual = bbox[3] - bbox[1]

    # Calculate text position (vertically centered, to the right of logo)
    text_x = logo_width + margin
    text_y = (new_height - text_height_actual) // 2

    # Draw text with gradient effect (simulate by using orange color)
    # Main text color - orange gradient middle color
    text_color = (249, 168, 37, 255)  # #F9A825 (orange)

    draw.text((text_x, text_y), text, font=font, fill=text_color)

    # Save the combined logo
    output_path = 'frontend/images/logo/coinpulse-logo-combined.png'
    combined.save(output_path)
    print(f"Created combined logo: {output_path}")
    print(f"   Size: {combined.size[0]}x{combined.size[1]} pixels")

    # Create a smaller version for navbar (height 60px)
    navbar_height = 60
    aspect_ratio = combined.size[0] / combined.size[1]
    navbar_width = int(navbar_height * aspect_ratio)
    navbar_logo = combined.resize((navbar_width, navbar_height), Image.Resampling.LANCZOS)
    navbar_path = 'frontend/images/logo/coinpulse-logo-navbar.png'
    navbar_logo.save(navbar_path)
    print(f"Created navbar logo: {navbar_path}")
    print(f"   Size: {navbar_logo.size[0]}x{navbar_logo.size[1]} pixels")

    # Create a smaller version for sidebar (height 40px)
    sidebar_height = 40
    sidebar_width = int(sidebar_height * aspect_ratio)
    sidebar_logo = combined.resize((sidebar_width, sidebar_height), Image.Resampling.LANCZOS)
    sidebar_path = 'frontend/images/logo/coinpulse-logo-sidebar.png'
    sidebar_logo.save(sidebar_path)
    print(f"Created sidebar logo: {sidebar_path}")
    print(f"   Size: {sidebar_logo.size[0]}x{sidebar_logo.size[1]} pixels")

    return output_path

if __name__ == '__main__':
    print("Creating CoinPulse combined logo...")
    create_combined_logo()
    print("Done!")
