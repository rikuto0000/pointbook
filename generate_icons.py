#!/usr/bin/env python3
"""
Generate PWA icons from SVG source
Requires: Pillow, cairosvg
Install: pip install Pillow cairosvg
"""

import os
from PIL import Image
import io

# Try to import cairosvg, if not available, create placeholder icons
try:
    import cairosvg
    HAS_CAIRO = True
except ImportError:
    print("cairosvg not installed. Creating placeholder icons instead.")
    print("To generate proper icons, run: pip install cairosvg")
    HAS_CAIRO = False

def create_placeholder_icon(size):
    """Create a simple placeholder icon using PIL only"""
    # Create new image with dark background
    img = Image.new('RGBA', (size, size), (15, 25, 35, 255))
    
    # Draw a simple crosshair using PIL
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(img)
    
    # Draw outer circle
    margin = size // 10
    draw.ellipse([margin, margin, size-margin, size-margin], 
                 outline=(255, 70, 85, 255), width=max(2, size//50))
    
    # Draw crosshair lines
    center = size // 2
    line_width = max(2, size // 40)
    line_length = size // 3
    
    # Vertical line
    draw.rectangle([center - line_width, center - line_length, 
                   center + line_width, center - line_width], 
                   fill=(255, 70, 85, 255))
    draw.rectangle([center - line_width, center + line_width, 
                   center + line_width, center + line_length], 
                   fill=(255, 70, 85, 255))
    
    # Horizontal line
    draw.rectangle([center - line_length, center - line_width, 
                   center - line_width, center + line_width], 
                   fill=(255, 70, 85, 255))
    draw.rectangle([center + line_width, center - line_width, 
                   center + line_length, center + line_width], 
                   fill=(255, 70, 85, 255))
    
    # Center dot
    dot_size = max(4, size // 20)
    draw.ellipse([center - dot_size, center - dot_size, 
                  center + dot_size, center + dot_size], 
                  fill=(255, 255, 255, 255))
    
    # Add "P" text
    try:
        # Try to use a bold font
        font_size = size // 4
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
    
    text = "P"
    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = (size - text_width) // 2
    text_y = center - text_height // 2 + size // 20
    
    draw.text((text_x, text_y), text, fill=(255, 255, 255, 200), font=font)
    
    return img

def generate_icon(size, output_path):
    """Generate an icon of specified size"""
    
    if HAS_CAIRO:
        # Convert SVG to PNG using cairosvg
        svg_path = os.path.join(os.path.dirname(__file__), 'static', 'icons', 'icon.svg')
        
        if os.path.exists(svg_path):
            try:
                # Convert SVG to PNG bytes
                png_data = cairosvg.svg2png(
                    url=svg_path,
                    output_width=size,
                    output_height=size
                )
                
                # Create PIL Image from bytes
                img = Image.open(io.BytesIO(png_data))
            except Exception as e:
                print(f"Error converting SVG: {e}")
                img = create_placeholder_icon(size)
        else:
            print(f"SVG file not found at {svg_path}")
            img = create_placeholder_icon(size)
    else:
        # Create placeholder icon
        img = create_placeholder_icon(size)
    
    # Save the image
    img.save(output_path, 'PNG')
    print(f"Generated: {output_path} ({size}x{size})")

def main():
    """Generate all required icon sizes"""
    
    # Define icon sizes for PWA
    sizes = [
        (16, 'favicon-16x16.png'),
        (32, 'favicon-32x32.png'),
        (72, 'icon-72.png'),
        (96, 'icon-96.png'),
        (128, 'icon-128.png'),
        (144, 'icon-144.png'),
        (152, 'icon-152.png'),
        (192, 'icon-192.png'),
        (384, 'icon-384.png'),
        (512, 'icon-512.png'),
    ]
    
    # Output directory
    output_dir = os.path.join(os.path.dirname(__file__), 'static', 'icons')
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate each icon size
    for size, filename in sizes:
        output_path = os.path.join(output_dir, filename)
        generate_icon(size, output_path)
    
    # Create a favicon.ico with multiple sizes
    favicon_sizes = [16, 32, 48]
    favicon_images = []
    
    for size in favicon_sizes:
        if HAS_CAIRO:
            svg_path = os.path.join(os.path.dirname(__file__), 'static', 'icons', 'icon.svg')
            if os.path.exists(svg_path):
                try:
                    png_data = cairosvg.svg2png(
                        url=svg_path,
                        output_width=size,
                        output_height=size
                    )
                    img = Image.open(io.BytesIO(png_data))
                except:
                    img = create_placeholder_icon(size)
            else:
                img = create_placeholder_icon(size)
        else:
            img = create_placeholder_icon(size)
        
        favicon_images.append(img)
    
    # Save as ICO
    favicon_path = os.path.join(output_dir, 'favicon.ico')
    favicon_images[0].save(
        favicon_path,
        format='ICO',
        sizes=[(16, 16), (32, 32), (48, 48)]
    )
    print(f"Generated: {favicon_path} (multi-size ICO)")
    
    print("\n✅ All icons generated successfully!")
    print(f"📁 Icons saved to: {output_dir}")

if __name__ == "__main__":
    main()