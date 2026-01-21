"""
PROJECT SINGULARITY: VOLUMETRIC BLACK HOLE RENDERER
Architect: N_BHARATH
Method: Ray Marching Approximation (Domain Warping + Simplex Noise)
Output: Photorealistic 800x600 Render

Overview:
Simulates an accretion disk around a Schwarzschild black hole using gravitational lensing
math applied to a procedural noise texture. Uses pure NumPy for vectorization.
"""

import math
import sys
import json
import random
import time
from datetime import datetime

try:
    import numpy as np
    from PIL import Image, ImageFilter, ImageEnhance, ImageOps, ImageDraw
except ImportError:
    print("CRITICAL: NumPy or Pillow missing. Install via pip.")
    sys.exit(1)

# --- OPENSIMPLEX NOISE IMPLEMENTATION (Pure Python/NumPy friendly) ---
# We use a simple noise generator to avoid external C dependencies like 'opensimplex'
# to ensure it runs on standard GitHub Actions runners without compilation issues.

class SimpleNoise:
    """A vectorized value noise generator using NumPy."""
    def __init__(self, width, height, seed=42):
        self.width = width
        self.height = height
        np.random.seed(seed)
        
        # Grid size for noise
        self.grid_w = 64
        self.grid_h = 64
        
        # Random gradients
        self.gradients = np.random.rand(self.grid_h + 1, self.grid_w + 1)

    def generate(self, zoom=1.0, offset_x=0.0):
        """Generates a noise texture of (height, width)."""
        # Coordinate grid
        x = np.linspace(0, self.grid_w * zoom, self.width) + offset_x
        y = np.linspace(0, self.grid_h * zoom, self.height)
        
        xv, yv = np.meshgrid(x, y)
        
        # Integer and fractional parts
        xi = xv.astype(int) % self.grid_w
        yi = yv.astype(int) % self.grid_h
        xf = xv - xv.astype(int)
        yf = yv - yv.astype(int)
        
        # Smooth interpolation (Fade function)
        u = xf * xf * (3.0 - 2.0 * xf)
        v = yf * yf * (3.0 - 2.0 * yf)
        
        # Hash / Gradient lookup
        # Simple value noise scalar interpolation
        g00 = self.gradients[yi, xi]
        g10 = self.gradients[yi, xi + 1]
        g01 = self.gradients[yi + 1, xi]
        g11 = self.gradients[yi + 1, xi + 1]
        
        # Bilinear interpolation
        n = (g00 * (1 - u) + g10 * u) * (1 - v) + \
            (g01 * (1 - u) + g11 * u) * v
            
        return n

class BlackHoleEngine:
    def __init__(self, state_file="state.json"):
        self.width = 800
        self.height = 600
        self.center = (self.width / 2, self.height / 2)
        self.state = self._load_state(state_file)
        
        # Physics Constants
        self.schwarzschild_radius = 80.0  # Event horizon size
        self.accretion_radius = 280.0    # Outer disk edge
        self.lensing_strength = 60.0    # How much light bends
        
        print(f">> INITIALIZING SINGULARITY ENGINE")
        print(f"   State: Probe={self.state.get('probe_status', 'STANDBY')}")

    def _load_state(self, path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"probe_status": "STANDBY", "energy": 100, "zoom": 1.0}

    def _generate_accretion_disk(self):
        """Generates the base texture for the accretion disk."""
        print("   Generating Accretion Noise Field...")
        
        noise = SimpleNoise(self.width, self.height, seed=int(time.time()))
        
        # Layered FBM (Fractal Brownian Motion)
        base = noise.generate(zoom=0.5, offset_x=random.random() * 10)
        detail = noise.generate(zoom=1.5, offset_x=random.random() * 10)
        micro = noise.generate(zoom=3.0, offset_x=random.random() * 10)
        
        # Combine
        texture = base * 0.6 + detail * 0.3 + micro * 0.1
        
        # Apply Ring Mask (cut out hole and outer edge)
        y, x = np.ogrid[:self.height, :self.width]
        dist_sq = (x - self.center[0])**2 + (y - self.center[1])**2
        dist = np.sqrt(dist_sq)
        
        # Accretion Disk Band
        # Smooth inner edge at 2.5 * Rs, outer at accretion_radius
        rs = self.schwarzschild_radius
        inner_edge = rs * 2.2
        outer_edge = self.accretion_radius
        
        # Soft edges
        mask = np.zeros_like(dist)
        # Gradient from inner to outer
        disk_region = (dist > inner_edge) & (dist < outer_edge)
        
        # Normalize distance within disk for texture mapping
        # 0 at inner, 1 at outer
        norm_dist = (dist - inner_edge) / (outer_edge - inner_edge)
        norm_dist = np.clip(norm_dist, 0, 1)
        
        # Density profile (bright in middle, fade out)
        density = np.sin(norm_dist * np.pi) ** 2
        
        # Apply mask
        final_texture = texture * density
        
        # Add "Gap" noise (swirls)
        swirl = np.sin(np.arctan2(y - self.center[1], x - self.center[0]) * 5 + norm_dist * 10)
        final_texture *= (0.8 + 0.2 * swirl)
        
        return final_texture, dist

    def _apply_lensing(self, texture, dist):
        """Applies gravitational lensing distortion."""
        print("   Bending Light (Gravitational Lensing)...")
        # Einstein Ring distortion: Light closest to event horizon is pulled in
        # Lensing shifts pixels radially OUTWARD visually (because light from BEHIND is pulled IN)
        # Actually, for a top-down/angled view implementation in 2D:
        # We simulate the visual appearance of the disk being bent UP over the top.
        
        # Simply: Pixels closer to center get "smudged" around the event horizon.
        # But for this 2.5D render, let's keep it clean:
        # We rely on the texture generation being circular.
        # Real lensing flips the back of the disk to the top.
        
        # Let's add a "Top Arch" (the back of the disk visible above the black hole)
        rs = self.schwarzschild_radius
        
        y, x = np.ogrid[:self.height, :self.width]
        
        # Define the Arch geometry
        # An ellipse placed slightly above center
        arch_y = self.center[1] - rs * 1.2
        arch_mask = ((x - self.center[0])**2 / (rs * 2.5)**2 + (y - arch_y)**2 / (rs * 0.8)**2) <= 1.0
        # Cut out the bottom part (behind the hole)
        arch_mask &= (y < self.center[1] - rs * 0.2)
        
        # Add the arch to the texture
        lensed_texture = texture.copy()
        
        # Make the arch slightly dimmer and redder (Doppler)
        # We'll handle color later, just intensity here
        lensed_texture[arch_mask] = np.maximum(lensed_texture[arch_mask], 0.5)
        
        return lensed_texture

    def _render_probe(self, img):
        """Renders the orbiting probe if active."""
        if self.state.get("probe_status") != "ACTIVE":
            return img
            
        print("   Detecting Active Probe signal...")
        draw = ImageDraw.Draw(img)
        
        # Calculate position (orbit)
        # Time-based or random based on state update count?
        # Let's put it on an elliptical orbit
        t = time.time() % 10
        angle = t * 0.5
        
        rx = self.schwarzschild_radius * 3.5
        ry = self.schwarzschild_radius * 1.5
        
        px = self.center[0] + math.cos(angle) * rx
        py = self.center[1] + math.sin(angle) * ry
        
        # Draw Probe Body
        r = 3
        draw.ellipse([px-r, py-r, px+r, py+r], fill=(0, 255, 0)) # Neon Green
        
        # Draw Trail/Glow
        # We can simulate trail by drawing fading dots
        for i in range(1, 10):
            trail_angle = angle - (i * 0.1)
            tx = self.center[0] + math.cos(trail_angle) * rx
            ty = self.center[1] + math.sin(trail_angle) * ry
            alpha = int(255 * (1 - i/10))
            draw.ellipse([tx-1, ty-1, tx+1, ty+1], fill=(0, 255, 0)) # Simple dot
            
        return img

    def render(self):
        print(">> RENDERING SINGULARITY...")
        
        # 1. Physics Calculations
        texture, dist_map = self._generate_accretion_disk()
        texture = self._apply_lensing(texture, dist_map)
        
        # 2. Color Grading (Doppler Shift)
        print("   Applying Doppler Shift & Tone Mapping...")
        H, W = self.height, self.width
        r_ch = np.zeros((H, W))
        g_ch = np.zeros((H, W))
        b_ch = np.zeros((H, W))
        
        # Background Void
        r_ch[:] = 13 # #0d1117
        g_ch[:] = 17
        b_ch[:] = 23
        
        # Doppler Shift Logic:
        # Left side (x < center) is moving TOWARDS -> Blue/White/Bright
        # Right side (x > center) is moving AWAY -> Red/Dim
        
        y, x = np.ogrid[:H, :W]
        norm_x = (x - self.center[0]) / (self.width / 2) # -1 to 1
        
        # Shift factor: -1 (Left) to 1 (Right)
        # Left: Boost Blue, Boost Intensity
        # Right: Boost Red, Reduce Intensity
        
        # Intensity Modulation
        doppler_intensity = 1.0 - 0.5 * norm_x # 1.5 on left, 0.5 on right
        
        final_intensity = texture * doppler_intensity
        
        # Color Mapping
        # Accretion Disk Base Color: Deep Orange (255, 100, 0)
        # Hot (Left): shift to White/Blue (200, 200, 255)
        # Cold (Right): shift to Deep Red (150, 20, 0)
        
        # Mask for disk
        valid = final_intensity > 0.05
        
        # R Channel
        r_ch[valid] += final_intensity[valid] * 255
        
        # Expand norm_x to matched shape for indexing
        # norm_x is currently (1, W). valid is (H, W).
        # We need the full 2D norm_x grid.
        norm_x_2d = np.tile(norm_x, (H, 1))
        
        # G Channel (Left side gets more Green -> Yellow -> White)
        g_factor = np.clip(1.0 - (norm_x_2d[valid] + 1) / 2, 0, 1) # 1 on left, 0 on right
        g_ch[valid] += final_intensity[valid] * (100 + 155 * g_factor)
        
        # B Channel (Only extreme left gets Blue)
        b_factor = np.clip(-norm_x_2d[valid], 0, 1) # 1 on far left, 0 elsewhere
        b_ch[valid] += final_intensity[valid] * (255 * b_factor)
        
        # 3. Event Horizon (The Void)
        # Hard cut in the middle
        rs = self.schwarzschild_radius
        horizon_mask = dist_map < rs
        
        # Pure Black hole
        r_ch[horizon_mask] = 0
        g_ch[horizon_mask] = 0
        b_ch[horizon_mask] = 0
        
        # Photon Ring (Bright thin ring around horizon)
        ring_mask = (dist_map >= rs) & (dist_map < rs * 1.05)
        r_ch[ring_mask] = 255
        g_ch[ring_mask] = 255
        b_ch[ring_mask] = 255
        
        # Clip
        rgb = np.dstack((r_ch, g_ch, b_ch))
        rgb = np.clip(rgb, 0, 255).astype(np.uint8)
        
        img = Image.fromarray(rgb)
        
        # 4. Post-Processing: Bloom & Glow
        print("   Post-Processing: Bloom & Tone Mapping...")
        # Create Glow Layer
        glow = img.filter(ImageFilter.GaussianBlur(radius=10))
        # Additive blend
        img = Image.blend(img, glow, 0.5)
        
        # Second pass wide bloom
        wide_glow = img.filter(ImageFilter.GaussianBlur(radius=30))
        img = Image.blend(img, wide_glow, 0.3)
        
        # 5. Render Probe
        img = self._render_probe(img)
        
        # 6. HUD Overlay
        # (Optional: Drawn here or in README? README is better for text, 
        # but let's draw scanlines for effect)
        scanlines = Image.new("RGBA", (W, H), (0,0,0,0))
        d = ImageDraw.Draw(scanlines)
        for i in range(0, H, 4):
            d.line([(0, i), (W, i)], fill=(0, 0, 0, 50))
        
        img.paste(scanlines, (0,0), scanlines)
        
        return img

def main():
    engine = BlackHoleEngine()
    final_image = engine.render()
    final_image.save("assets/blackhole.png")
    print(">> ASSET SECURED: assets/blackhole.png")

if __name__ == "__main__":
    main()
