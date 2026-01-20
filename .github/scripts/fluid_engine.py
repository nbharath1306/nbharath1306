"""
PROJECT AETHER: LATTICE BOLTZMANN FLUID DYNAMICS ENGINE
Architect: N_BHARATH
Model: D2Q9 (2D, 9 Velocities)
Method: Single-Relaxation-Time (SRT) BGK Collision

Overview:
Simulates fluid flow around obstacles using microscopic particle distribution functions.
This script is optimized for CPU execution using NumPy vectorization.
"""

import math
import argparse
import random
from typing import Tuple

# Try to import essential scientific libraries
try:
    import numpy as np
    from PIL import Image, ImageFilter, ImageEnhance, ImageOps
except ImportError:
    print("CRITICAL: NumPy or Pillow missing. Install via pip.")
    exit(1)

# --- PHYSICAL CONSTANTS ---
# D2Q9 Constants
# Directions: 0:Center, 1:E, 2:N, 3:W, 4:S, 5:NE, 6:NW, 7:SW, 8:SE
N_ROWS = 100
N_COLS = 300
Q = 9  # 9 discrete velocities

# Weights for D2Q9
W = np.array([4/9, 1/9, 1/9, 1/9, 1/9, 1/36, 1/36, 1/36, 1/36])

# Discrete velocities (c_x, c_y)
CX = np.array([0, 1, 0, -1, 0, 1, -1, -1, 1])
CY = np.array([0, 0, 1, 0, -1, 1, 1, -1, -1])

# Indices of opposite directions (for bounce-back boundary conditions)
OPPOSITE = np.array([0, 3, 4, 1, 2, 7, 8, 5, 6])


class AetherEngine:
    def __init__(self, viscosity=0.02, width=300, height=100):
        self.width = width
        self.height = height
        
        # Simulation Parameters
        # Relaxation time (tau) relates to viscosity (nu): nu = (tau - 0.5) / 3
        # tau = 3 * nu + 0.5
        self.nu = viscosity
        self.tau = 3.0 * self.nu + 0.5
        self.omega = 1.0 / self.tau # Relaxation frequency
        
        print(f">> INITIALIZING AETHER KERNEL: Grid={width}x{height}, Viscosity={viscosity}, Omega={self.omega:.4f}")

        # Initialize Distribution Functions
        # f[y, x, i] is density of particles at (x,y) moving in direction i
        self.f = np.zeros((height, width, Q))
        
        # Macroscopic variables
        self.rho = np.ones((height, width)) # Density, start at 1.0
        self.u = np.zeros((height, width, 2)) # Velocity vector (ux, uy)
        
        # Obstacle Mask (Boolean: True = solid)
        self.mask = np.zeros((height, width), dtype=bool)
        self._create_obstacles()
        
        # Initialize equilibrium
        self._init_equilibrium()

    def _create_obstacles(self):
        """Places a cylinder/circle obstacle in the flow to create turbulence."""
        cx, cy = self.width // 4, self.height // 2
        radius = self.height // 8
        
        y, x = np.ogrid[:self.height, :self.width]
        dist_sq = (x - cx)**2 + (y - cy)**2
        self.mask = dist_sq <= radius**2
        
        # Add random smaller debris for extra chaos
        # Deterministic random for reproducibility if needed, but we want chaos
        np.random.seed(42) 
        for _ in range(5):
             rx = np.random.randint(self.width // 3, self.width - 20)
             ry = np.random.randint(10, self.height - 10)
             r_size = np.random.randint(2, 6)
             dist_sq = (x - rx)**2 + (y - ry)**2
             self.mask |= (dist_sq <= r_size**2)

    def _init_equilibrium(self):
        """Sets f to f_eq based on initial velocity (light breeze to right)."""
        u0 = 0.1 # Initial speed
        self.u[:, :, 0] = u0 # x-velocity
        self.u[:, :, 1] = 0.0 # y-velocity
        
        # Add minimal noise to break symmetry immediately
        noise = np.random.rand(self.height, self.width, 2) * 0.01 
        self.u += noise
        
        self.f = self._compute_equilibrium(self.rho, self.u)

    def _compute_equilibrium(self, rho, u):
        """
        Computes f_eq according to D2Q9 model.
        f_eq_i = w_i * rho * (1 + 3(c_i . u) + 4.5(c_i . u)^2 - 1.5(u . u))
        """
        # Vectorized implementation
        # u is (H, W, 2)
        # We need dot products for each of the 9 directions
        
        # Magnitude squared of u: u.u (H, W)
        usq = u[:,:,0]**2 + u[:,:,1]**2
        
        feq = np.zeros((self.height, self.width, Q))
        
        for i in range(Q):
            # Dot product c_i . u
            cu = CX[i] * u[:,:,0] + CY[i] * u[:,:,1]
            
            # The expansion
            term1 = 3.0 * cu
            term2 = 4.5 * (cu * cu)
            term3 = 1.5 * usq
            
            feq[:,:,i] = W[i] * rho * (1.0 + term1 + term2 - term3)
            
        return feq

    def step(self):
        """Executes one LBM time step: Collision -> Streaming -> Boundary."""
        
        # 1. Macroscopic Moment Calculation
        # rho = sum(f_i)
        self.rho = np.sum(self.f, axis=2)
        
        # u = sum(f_i * c_i) / rho
        # Faster way to calculate u . rho without division yet
        ux_rho = np.sum(self.f * CX, axis=2)
        uy_rho = np.sum(self.f * CY, axis=2)
        
        # Update Velocity (avoid division by zero, though rho ~ 1)
        self.u[:,:,0] = ux_rho / self.rho
        self.u[:,:,1] = uy_rho / self.rho
        
        # Force inlet (left side) to have steady flow
        u_inlet = 0.1
        self.u[:, 0, 0] = u_inlet
        self.u[:, 0, 1] = 0.0
        self.rho[:, 0] = 1.0
        
        # Recompute equilibrium for inlet specifically
        # (This acts as the driving force)
        f_inlet = self._compute_equilibrium(self.rho[:, 0:1], self.u[:, 0:1])
        # We generally only enforce equilibrium at inlet for simplicity in this demo
        # But let's just use the collision step to drive it naturally 
        # by fixing the f distribution at x=0
        for i in range(Q):
            self.f[:, 0, i] = f_inlet[:, 0, i]

        # 2. Collision (BGK)
        # f_out = f_in - omega * (f_in - f_eq)
        feq = self._compute_equilibrium(self.rho, self.u)
        self.f = self.f - self.omega * (self.f - feq)
        
        # 3. Streaming
        # Shift data in memory using np.roll
        for i in range(Q):
             # shift(array, shift, axis)
             # if CX=1, we shift columns right (+1)
             # We actually strictly want f(x + cx) = f(x) from prev.
             # So we roll by cx, cy.
             self.f[:, :, i] = np.roll(self.f[:, :, i], shift=CX[i], axis=1)
             self.f[:, :, i] = np.roll(self.f[:, :, i], shift=CY[i], axis=0)
             
        # 4. Boundary Conditions
        # Bounce-back on obstacles
        # Rigid body logic: reflect distribution functions
        if self.mask.any():
            bounced_f = self.f[self.mask]
            # For each direction, the new f is the old f from opposite direction
            # But "old" f is what flowed IN to the wall.
            # Due to streaming, the f values are now AT the wall position.
            # We explicitly reverse them.
            # Effectively: f_i_new = f_opposite_i_old
            # We can just swap indices in the masked region.
            for i in range(Q):
                # This simple swap logic works for stationary walls after streaming
                self.f[self.mask, i] = bounced_f[:, OPPOSITE[i]]
        
        # Simple outlet (right side) - open boundary (gradient = 0)
        self.f[:, -1, :] = self.f[:, -2, :]


class Visualizer:
    @staticmethod
    def compute_curl(u, width, height):
        """Calculates vorticity (curl) = du_y/dx - du_x/dy."""
        # Use simple gradient from numpy
        # u shape (H, W, 2)
        uy = u[:,:,1]
        ux = u[:,:,0]
        
        # Gradient returns list of arrays [gradient_axis_0 (y), gradient_axis_1 (x)]
        guy = np.gradient(uy, axis=(0,1)) 
        duy_dx = guy[1]
        
        gux = np.gradient(ux, axis=(0,1))
        dux_dy = gux[0]
        
        curl = duy_dx - dux_dy
        return curl

    @staticmethod
    def render_frame(engine, upscale_factor=3):
        """Renders the current state to a PIL Image."""
        
        # 1. Physics Data Analysis
        # We visualize Curl (Vorticity) for swirliness + Velocity Magnitude for speed
        curl = Visualizer.compute_curl(engine.u, engine.width, engine.height)
        speed = np.sqrt(engine.u[:,:,0]**2 + engine.u[:,:,1]**2)
        
        # Normalize for visualization
        # Curl usually ranges -0.1 to 0.1 in these sims at this scale
        # We want absolute curl to drive "Turbulence" visibility
        abs_curl = np.abs(curl)
        
        # Normalize 0..1 roughly
        norm_curl = np.clip(abs_curl * 20.0, 0, 1)
        norm_speed = np.clip(speed * 3.0, 0, 1)
        
        # 2. Construct Canvas
        # We will build channels R, G, B
        H, W = engine.height, engine.width
        r_channel = np.zeros((H, W))
        g_channel = np.zeros((H, W))
        b_channel = np.zeros((H, W))
        
        # COLOR MAPPING: "Cyber-Liquid"
        # Background: #0d1117 (Dark) -> R:13 G:17 B:23
        bg_r, bg_g, bg_b = 13, 17, 23
        
        # High Curl -> Neon Purple (#bd00ff) -> R:189 G:0 B:255
        # High Speed -> Neon Cyan (#00f3ff) -> R:0 G:243 B:255
        
        # Mix factor based on curl presence
        # If static, use background
        # If moving, blend in Cyan
        # If spinning, blend in Purple
        
        # Base luminance
        r_channel[:] = bg_r
        g_channel[:] = bg_g
        b_channel[:] = bg_b
        
        # Add Cyan based on speed
        r_channel += norm_speed * 0   # Cyan has 0 red
        g_channel += norm_speed * 200 # Cyan G
        b_channel += norm_speed * 220 # Cyan B
        
        # Add Purple based on Curl (Spinning)
        # This overrides/adds to speed
        r_channel += norm_curl * 180 # Purple R
        g_channel -= norm_curl * 50  # Remove Green to make it purple
        b_channel += norm_curl * 100 # Purple B
        
        # Mask Obstacles (Solid Black/Grey)
        mask = engine.mask
        r_channel[mask] = 50
        g_channel[mask] = 50
        b_channel[mask] = 50
        
        # Clip to 0-255
        r_channel = np.clip(r_channel, 0, 255).astype(np.uint8)
        g_channel = np.clip(g_channel, 0, 255).astype(np.uint8)
        b_channel = np.clip(b_channel, 0, 255).astype(np.uint8)
        
        # Stack
        rgb = np.dstack((r_channel, g_channel, b_channel))
        img = Image.fromarray(rgb, mode='RGB')
        
        # 3. Post-Processing
        # Upscale
        target_size = (W * upscale_factor, H * upscale_factor)
        img = img.resize(target_size, resample=Image.Resampling.BICUBIC)
        
        # Bloom/Glow Effect
        # Create a blurred copy
        glow = img.filter(ImageFilter.GaussianBlur(radius=5))
        # Blend: Screen or Add. PIL 'lighter' is roughly max. 
        # Let's simple blend with alpha
        img = Image.blend(img, glow, alpha=0.5)
        
        # Enhance Contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)
        
        return img


def run_simulation():
    print(">> ENGAGING AETHER FLUID SIMULATION")
    
    # 1. Setup
    sim = AetherEngine(viscosity=0.02, width=300, height=100)
    
    # 2. Warmup (Establish flow)
    print(">> WARMING UP (500 steps)...")
    for s in range(500):
        sim.step()
        if s % 100 == 0:
            print(f"   ... step {s}")
            
    # 3. Recording Phase
    print(">> RECORDING SEQUENCE (60 frames)...")
    frames = []
    
    for s in range(60):
        sim.step()
        # Render
        frame = Visualizer.render_frame(sim, upscale_factor=3)
        frames.append(frame)
        if s % 10 == 0:
            print(f"   ... captured frame {s}")
            
    # 4. Save Artifact
    print(">> COMPILING GIF ARTIFACT...")
    frames[0].save(
        "assets/aether.gif",
        save_all=True,
        append_images=frames[1:],
        duration=30, # ~30fps visual style for fluid
        loop=0
    )
    print(">> ASSET SECURED: assets/aether.gif")

if __name__ == "__main__":
    run_simulation()
