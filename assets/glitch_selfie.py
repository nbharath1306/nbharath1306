from PIL import Image, ImageEnhance, ImageOps
import random
import os

def create_glitch_gif(source_path, output_path, frames=10):
    print(f"Reading source: {source_path}")
    try:
        original = Image.open(source_path).convert("RGB")
    except Exception as e:
        print(f"Error loading image: {e}")
        return

    # Resize to something manageable for a profile GIF
    # Maintain aspect ratio but max width 400
    base_width = 400
    w_percent = (base_width / float(original.size[0]))
    h_size = int((float(original.size[1]) * float(w_percent)))
    original = original.resize((base_width, h_size), Image.Resampling.LANCZOS)
    
    # Pre-process: High contrast, cool tone
    enhancer = ImageEnhance.Contrast(original)
    original = enhancer.enhance(1.2)
    
    # Color grading (Green Tint for Circle-13)
    r, g, b = original.split()
    g = g.point(lambda i: i * 1.1)
    original = Image.merge("RGB", (r, g, b))

    sequence = []

    for i in range(frames):
        # Create a copy
        frame = original.copy()
        
        # 1. Channel Shift (RGB Split)
        # Shift Red channel left, Blue channel right
        shift_amount = random.randint(2, 6)
        r, g, b = frame.split()
        
        r = ImageOps.crop(r, (shift_amount, 0, 0, 0))
        r = ImageOps.expand(r, (0, 0, shift_amount, 0), fill=0)
        
        b = ImageOps.crop(b, (0, 0, shift_amount, 0))
        b = ImageOps.expand(b, (shift_amount, 0, 0, 0), fill=0)
        
        glitched = Image.merge("RGB", (r, g, b))
        
        # 2. Scanlines
        # Darken every 4th line
        pixels = glitched.load()
        for y in range(0, glitched.height, 4):
            for x in range(glitched.width):
                r, g, b = pixels[x, y]
                pixels[x, y] = (int(r*0.7), int(g*0.7), int(b*0.7))

        # 3. Random noise blocks
        if random.random() > 0.6:
            block_h = random.randint(5, 20)
            block_y = random.randint(0, glitched.height - block_h)
            
            # Simple box swap or invert
            box = (0, block_y, glitched.width, block_y + block_h)
            region = glitched.crop(box)
            region = ImageOps.invert(region)
            glitched.paste(region, box)

        sequence.append(glitched)

    # Save as GIF
    sequence[0].save(
        output_path,
        save_all=True,
        append_images=sequence[1:],
        duration=100, # 100ms per frame = 10fps
        loop=0
    )
    print(f"Generated: {output_path}")

if __name__ == "__main__":
    create_glitch_gif("assets/source.jpg", "assets/profile.gif")
