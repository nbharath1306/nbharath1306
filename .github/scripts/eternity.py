"""
PROJECT ETERNITY: PARTICLE MORPHING ENGINE
Architect: N_BHARATH
Simulation: Swarm Intelligence + Steering Behaviors
Visual: Nanotech Assembly Effect

Overview:
5000 particles morph from chaos into the user's name, hold, then explode into a galaxy.
Physics are fully vectorized using NumPy. No Python loops for particle updates.
"""

import os
import math
import random
from typing import Tuple, List

try:
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except ImportError:
    print("CRITICAL: NumPy or Pillow missing. Install via pip.")
    exit(1)

# --- CONFIGURATION ---
CONFIG = {
    "width": 800,
    "height": 300,
    "particle_count": 5000,
    "total_frames": 100,
    "fps": 30,
    "bg_color": (13, 17, 23),  # #0d1117
    "text": "N BHARATH",
    "font_size": 80,
    "font_path": "Roboto-Bold.ttf",  # Downloaded in workflow
}

# Color Palette
GOLD = np.array([255, 215, 0])      # #FFD700
CYAN = np.array([0, 255, 255])      # #00FFFF
WHITE = np.array([255, 255, 255])


class TextTargetGenerator:
    """Generates target coordinates from text rendering."""
    
    @staticmethod
    def generate(text: str, width: int, height: int, font_path: str, font_size: int) -> np.ndarray:
        """
        Renders text to a mask and extracts pixel coordinates.
        Returns: np.ndarray of shape (N, 2) containing (x, y) coordinates.
        """
        print(f">> GENERATING TEXT TARGETS: '{text}'")
        
        # Create mask image
        mask = Image.new("L", (width, height), 0)
        draw = ImageDraw.Draw(mask)
        
        # Load font
        try:
            font = ImageFont.truetype(font_path, font_size)
        except OSError:
            print(f"   ! Font '{font_path}' not found. Using default.")
            font = ImageFont.load_default()
        
        # Calculate text position (centered)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        # Draw text
        draw.text((x, y), text, fill=255, font=font)
        
        # Convert to numpy and find white pixels
        mask_array = np.array(mask)
        coords = np.argwhere(mask_array > 128)  # (y, x) format
        
        # Swap to (x, y) and convert to float
        targets = coords[:, ::-1].astype(np.float64)
        
        print(f"   Found {len(targets)} target pixels")
        return targets


class Swarm:
    """The Particle Physics Engine."""
    
    def __init__(self, count: int, width: int, height: int):
        self.count = count
        self.width = width
        self.height = height
        self.center = np.array([width / 2, height / 2])
        
        # State Vectors (N, 2)
        # Initialize positions randomly across screen
        self.pos = np.random.rand(count, 2) * np.array([width, height])
        
        # Initialize velocities (small random)
        self.vel = (np.random.rand(count, 2) - 0.5) * 2
        
        # Targets (will be set per phase)
        self.targets = np.zeros((count, 2))
        
        # Particle properties
        self.brightness = np.ones(count)  # 0-1 brightness multiplier
        self.is_gold = np.random.rand(count) > 0.3  # 70% gold, 30% cyan
        
        print(f">> SWARM INITIALIZED: {count} particles")
    
    def assign_text_targets(self, text_coords: np.ndarray):
        """Assigns each particle a random target from text coordinates."""
        if len(text_coords) == 0:
            print("   ! No text coordinates. Using center.")
            self.targets = np.tile(self.center, (self.count, 1))
            return
            
        # Randomly sample from text coordinates
        indices = np.random.randint(0, len(text_coords), self.count)
        self.targets = text_coords[indices].copy()
        
        # Add small offset to prevent perfect overlap
        self.targets += np.random.randn(self.count, 2) * 0.5
    
    def assign_chaos_targets(self):
        """Assigns random screen positions as targets."""
        self.targets = np.random.rand(self.count, 2) * np.array([self.width, self.height])
    
    def assign_explosion_targets(self):
        """Assigns radial explosion targets from center."""
        # Random angles
        angles = np.random.rand(self.count) * 2 * np.pi
        # Random radii (push far out)
        radii = np.random.rand(self.count) * max(self.width, self.height) * 0.8
        
        self.targets[:, 0] = self.center[0] + np.cos(angles) * radii
        self.targets[:, 1] = self.center[1] + np.sin(angles) * radii
    
    def update(self, phase: str, dt: float = 1.0):
        """
        Vectorized physics update.
        Phase: 'chaos', 'form', 'hold', 'explode'
        """
        # --- STEERING FORCES ---
        
        # 1. Attraction to Target
        direction = self.targets - self.pos
        distance = np.linalg.norm(direction, axis=1, keepdims=True) + 0.001  # Avoid division by zero
        direction_normalized = direction / distance
        
        # Adjust force based on phase
        if phase == 'chaos':
            attraction_strength = 0.02
            max_speed = 3.0
            noise_strength = 2.0
        elif phase == 'form':
            attraction_strength = 0.15
            max_speed = 8.0
            noise_strength = 0.3
        elif phase == 'hold':
            attraction_strength = 0.3
            max_speed = 2.0
            noise_strength = 0.8  # Jitter in place
        elif phase == 'explode':
            attraction_strength = 0.08
            max_speed = 12.0
            noise_strength = 0.5
        else:
            attraction_strength = 0.1
            max_speed = 5.0
            noise_strength = 1.0
        
        # Apply attraction
        attraction_force = direction_normalized * attraction_strength
        self.vel += attraction_force
        
        # 2. Brownian Motion (Chaos / Jitter)
        noise = (np.random.rand(self.count, 2) - 0.5) * noise_strength
        self.vel += noise
        
        # 3. Damping (Friction)
        self.vel *= 0.92
        
        # 4. Speed Limit
        speed = np.linalg.norm(self.vel, axis=1, keepdims=True)
        mask = (speed > max_speed).flatten()
        self.vel[mask] = (self.vel[mask] / speed[mask]) * max_speed
        
        # --- UPDATE POSITION ---
        self.pos += self.vel * dt
        
        # --- BOUNDARY HANDLING (Soft Wrap) ---
        # Allow particles to go slightly off screen, they'll come back
        pass  # No hard clipping for now
        
        # --- UPDATE BRIGHTNESS (Pulse effect during hold) ---
        if phase == 'hold':
            # Base brightness + sinusoidal pulse
            pulse = 0.7 + 0.3 * np.sin(np.random.rand(self.count) * 2 * np.pi)
            self.brightness = pulse
        else:
            # Brightness based on speed (faster = brighter)
            self.brightness = np.clip(speed.flatten() / max_speed * 1.5, 0.3, 1.0)


class GlowEngine:
    """The Rendering Pipeline."""
    
    @staticmethod
    def render_frame(swarm: Swarm, width: int, height: int) -> Image.Image:
        """
        Renders particles to an image with glow effect.
        Uses direct NumPy array manipulation for speed.
        """
        # Create RGB canvas
        canvas = np.zeros((height, width, 3), dtype=np.float32)
        
        # Get particle data
        pos = swarm.pos
        brightness = swarm.brightness
        is_gold = swarm.is_gold
        
        # Filter particles within bounds (with margin for glow)
        margin = 3
        valid = (
            (pos[:, 0] >= -margin) & (pos[:, 0] < width + margin) &
            (pos[:, 1] >= -margin) & (pos[:, 1] < height + margin)
        )
        
        pos_valid = pos[valid]
        brightness_valid = brightness[valid]
        is_gold_valid = is_gold[valid]
        
        # Draw particles with 3x3 glow pattern
        # Center = full brightness, edges = 0.3x brightness
        glow_pattern = [
            (0, 0, 1.0),    # Center
            (-1, 0, 0.3),   # Left
            (1, 0, 0.3),    # Right
            (0, -1, 0.3),   # Top
            (0, 1, 0.3),    # Bottom
        ]
        
        for dx, dy, intensity in glow_pattern:
            # Calculate pixel coordinates
            px = (pos_valid[:, 0] + dx).astype(np.int32)
            py = (pos_valid[:, 1] + dy).astype(np.int32)
            
            # Filter to valid indices
            in_bounds = (px >= 0) & (px < width) & (py >= 0) & (py < height)
            px_valid = px[in_bounds]
            py_valid = py[in_bounds]
            b_valid = brightness_valid[in_bounds] * intensity
            gold_mask = is_gold_valid[in_bounds]
            
            # Calculate colors
            colors = np.where(
                gold_mask[:, np.newaxis],
                GOLD * b_valid[:, np.newaxis],
                CYAN * b_valid[:, np.newaxis]
            )
            
            # Additive blending (accumulate)
            # Use np.add.at for scatter-add operation
            np.add.at(canvas, (py_valid, px_valid), colors)
        
        # Clip to 0-255
        canvas = np.clip(canvas, 0, 255).astype(np.uint8)
        
        # Convert to PIL Image
        img = Image.fromarray(canvas)
        
        # Apply subtle blur for extra glow
        img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
        
        # Composite over background
        bg = Image.new("RGB", (width, height), CONFIG["bg_color"])
        # Blend: Screen-like effect (additive)
        final = Image.blend(bg, img, alpha=0.95)
        
        return final


def run_simulation():
    print(">> PROJECT ETERNITY: PARTICLE MORPHING ENGINE")
    print("=" * 50)
    
    width = CONFIG["width"]
    height = CONFIG["height"]
    total_frames = CONFIG["total_frames"]
    
    # 1. Generate Text Targets
    text_coords = TextTargetGenerator.generate(
        CONFIG["text"],
        width,
        height,
        CONFIG["font_path"],
        CONFIG["font_size"]
    )
    
    # 2. Initialize Swarm
    swarm = Swarm(CONFIG["particle_count"], width, height)
    
    # Pre-calculate text targets for reuse
    swarm.assign_text_targets(text_coords)
    text_targets_backup = swarm.targets.copy()
    
    # 3. Animation Loop
    frames = []
    
    # Phase Definitions
    # Chaos: 0-20, Form: 20-50, Hold: 50-70, Explode: 70-100
    print(">> SIMULATING PARTICLE DYNAMICS...")
    
    for f in range(total_frames):
        # Determine Phase
        if f < 20:
            phase = 'chaos'
            if f == 0:
                swarm.assign_chaos_targets()
        elif f < 50:
            phase = 'form'
            if f == 20:
                swarm.targets = text_targets_backup.copy()
        elif f < 70:
            phase = 'hold'
        else:
            phase = 'explode'
            if f == 70:
                swarm.assign_explosion_targets()
        
        # Update Physics
        swarm.update(phase)
        
        # Render Frame
        frame = GlowEngine.render_frame(swarm, width, height)
        frames.append(frame)
        
        if f % 20 == 0:
            print(f"   Frame {f}/{total_frames} [{phase}]")
    
    # 4. Save GIF
    print(">> COMPILING ANIMATION...")
    duration = int(1000 / CONFIG["fps"])  # ms per frame
    
    frames[0].save(
        "assets/eternity.gif",
        save_all=True,
        append_images=frames[1:],
        duration=duration,
        loop=0,
        optimize=False  # Faster save, slightly larger file
    )
    
    print(">> ASSET SECURED: assets/eternity.gif")
    print(">> PROJECT ETERNITY: COMPLETE")


if __name__ == "__main__":
    run_simulation()
