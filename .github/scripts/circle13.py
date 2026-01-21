import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random

# --- CONFIGURATION ---
WIDTH = 800
ACCENT_COLOR = "#67DD10" # Your Website's Green
BG_COLOR = "#0d1117"     # GitHub Dark Mode (Seamless blend)
TEXT_COLOR = "#FFFFFF"

def create_glitch_header():
    # 1. Setup Canvas
    height = 250
    img = Image.new('RGB', (WIDTH, height), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    # 2. Draw "SIGNAL ACQUIRED" Elements
    # Note: In a real environment, we'd load a font. Here we use default or simulated.
    # We will draw the "Brutalist" lines
    
    # Top Border
    draw.line([(0, 10), (WIDTH, 10)], fill=ACCENT_COLOR, width=2)
    
    # The Main Title: "CIRCLE 13"
    # We simulate a large pixelated font by drawing rectangles for text (Abstract representation)
    # OR we just draw clean text if font available. We'll assume a system font fallback.
    
    # Draw the "SYSTEM READY" text
    draw.text((20, 30), "SYSTEM READY 100%", fill=ACCENT_COLOR)
    draw.text((700, 30), "V.3.0", fill=ACCENT_COLOR)
    
    # The Massive "C-13" Logo (Draw manually for style)
    # Drawing a big hollow circle
    left_x = WIDTH // 2 - 60
    draw.ellipse([left_x, 60, left_x + 120, 180], outline="white", width=5)
    
    # The "13" inside
    draw.text((left_x + 40, 100), "13", fill="white") # Placeholder for the logo logic
    
    # The "Signal" Noise lines
    for i in range(0, height, 4):
        if random.random() > 0.8:
            width_line = random.randint(10, 100)
            start_x = random.randint(0, WIDTH)
            draw.line([(start_x, i), (start_x + width_line, i)], fill=(30, 30, 30), width=1)

    # 3. Save
    # We apply a slight blur to simulate a CRT screen
    img = img.filter(ImageFilter.GaussianBlur(0.5))
    img.save("assets/header.png")
    print("HEADER GENERATED.")

def create_manifesto_poster():
    # The "VOLUME NEGATES LUCK" Graphic
    height = 400
    img = Image.new('RGB', (WIDTH, height), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Big text logic (simulated)
    # "VOLUME"
    draw.text((50, 100), "VOLUME", fill="white") 
    # "NEGATES"
    draw.text((50, 150), "NEGATES", fill="white")
    # "LUCK"
    draw.text((50, 200), "LUCK", fill=ACCENT_COLOR)
    
    # The Decor
    draw.rectangle([50, 280, 150, 290], fill=ACCENT_COLOR)
    draw.text((50, 300), "WE DON'T BUILD ONE THING.", fill="gray")
    draw.text((50, 320), "WE BUILD EVERYTHING.", fill="gray")
    
    img.save("assets/manifesto.png")
    print("MANIFESTO GENERATED.")

if __name__ == "__main__":
    os.makedirs("assets", exist_ok=True)
    create_glitch_header()
    create_manifesto_poster()
