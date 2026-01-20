import math
import random
from PIL import Image, ImageDraw, ImageEnhance

# CONFIGURATION
WIDTH, HEIGHT = 800, 400
GRID_SIZE = 12
CUBE_SIZE = 30
FRAMES = 20  # Number of frames in the GIF

# PALETTE (CYBERPUNK CEO THEME)
TOP_COLOR = (20, 240, 255)    # Neon Cyan
SIDE_LEFT = (10, 100, 120)    # Dark Blue
SIDE_RIGHT = (5, 50, 60)      # Darker Blue
BG_COLOR = (13, 17, 23)       # GitHub Dark Mode Background (Exact Match)

def draw_cube(draw, x, y, size, height_scale, glow_intensity):
    """ Draws a single isometric building """
    # Isometric Math
    h = size * height_scale
    
    # Vertices
    top_v = (x, y - h)
    right_v = (x + size, y + size//2 - h)
    bottom_v = (x, y + size - h)
    left_v = (x - size, y + size//2 - h)
    base_bottom = (x, y + size)
    
    # Draw Sides (The Building)
    draw.polygon([left_v, bottom_v, base_bottom, (x - size, y + size//2)], fill=SIDE_LEFT)
    draw.polygon([right_v, bottom_v, base_bottom, (x + size, y + size//2)], fill=SIDE_RIGHT)
    
    # Draw Roof (The Light)
    # Varies brightness based on "glow_intensity" to simulate city lights breathing
    r, g, b = TOP_COLOR
    bright_color = (
        min(255, int(r * glow_intensity)),
        min(255, int(g * glow_intensity)),
        min(255, int(b * glow_intensity))
    )
    draw.polygon([top_v, right_v, bottom_v, left_v], fill=bright_color)

def generate_frame(frame_num):
    img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Center the grid
    center_x = WIDTH // 2
    center_y = HEIGHT // 4
    
    # Procedural Generation loop
    # In a full version, you would feed Repo Stats into 'h'
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            # Calculate isometric position
            iso_x = center_x + (col - row) * CUBE_SIZE
            iso_y = center_y + (col + row) * (CUBE_SIZE // 2)
            
            # Deterministic Randomness (Seeded by position so buildings stay still)
            random.seed(row * col + 99) 
            building_height = random.uniform(0.5, 4.0) 
            
            # Animation Logic (Breathing Effect)
            # Each building glows at a different phase
            phase = (frame_num / FRAMES) * 6.28 + (row + col)
            glow = 0.8 + 0.4 * math.sin(phase)
            
            draw_cube(draw, iso_x, iso_y, CUBE_SIZE - 2, building_height, glow)
            
    return img

# MAIN EXECUTION
print("Constructing Empire...")
frames = []
for i in range(FRAMES):
    frames.append(generate_frame(i))

# Save as GIF
frames[0].save(
    'empire.gif',
    save_all=True,
    append_images=frames[1:],
    duration=100,
    loop=0
)
print("Empire Built.")
