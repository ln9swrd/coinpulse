#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Create favicon.ico from logo
"""

from PIL import Image

def create_favicon():
    # Load the logo
    logo = Image.open('frontend/images/logo/coinpulse-logo.png')

    # Create different sizes for favicon
    # Standard sizes: 16x16, 32x32, 48x48
    sizes = [(16, 16), (32, 32), (48, 48)]

    # Convert to RGBA if not already
    if logo.mode != 'RGBA':
        logo = logo.convert('RGBA')

    # Create a square canvas with the logo centered
    # Get the logo dimensions
    logo_width, logo_height = logo.size

    # Create square canvas
    max_size = max(logo_width, logo_height)
    square_logo = Image.new('RGBA', (max_size, max_size), (0, 0, 0, 0))

    # Paste logo centered
    x_offset = (max_size - logo_width) // 2
    y_offset = (max_size - logo_height) // 2
    square_logo.paste(logo, (x_offset, y_offset), logo)

    # Create resized versions
    icon_images = []
    for size in sizes:
        resized = square_logo.resize(size, Image.Resampling.LANCZOS)
        icon_images.append(resized)

    # Save as favicon.ico
    output_path = 'frontend/favicon.ico'
    icon_images[0].save(
        output_path,
        format='ICO',
        sizes=sizes,
        append_images=icon_images[1:]
    )

    print(f"Created favicon.ico: {output_path}")
    print(f"Sizes: {', '.join([f'{s[0]}x{s[1]}' for s in sizes])}")

    return output_path

if __name__ == '__main__':
    print("Creating favicon.ico...")
    create_favicon()
    print("Done!")
