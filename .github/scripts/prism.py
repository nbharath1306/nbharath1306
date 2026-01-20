import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.animation as animation
import random
import datetime

# --- CONFIGURATION: THE HIGH-END AESTHETIC ---
# We use a "Cyber-Noir" palette: Deep Void Black + Neon Cyan + Electric Purple
CMAP_NAME = 'cyber_glass'
COLORS = ["#050505", "#1a1a2e", "#16213e", "#0f3460", "#e94560", "#00fff5"]
GRID_SIZE = 15  # 15 weeks of data
MAX_HEIGHT = 10 # Height of the tallest crystal

# 1. GENERATE THE DATA (YOUR DNA)
# In reality, this would fetch your commit graph. 
# We simulate a "Founder's Workload" (Spiky, intense bursts of code)
def generate_crystal_lattice():
    np.random.seed(int(datetime.datetime.now().timestamp()))
    x = np.arange(GRID_SIZE)
    y = np.arange(GRID_SIZE)
    X, Y = np.meshgrid(x, y)
    
    # Perlin-like noise simulation for organic growth
    Z = np.zeros((GRID_SIZE, GRID_SIZE))
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            dist = np.sqrt((i-GRID_SIZE/2)**2 + (j-GRID_SIZE/2)**2)
            Z[i,j] = np.abs(np.sin(i/2) * np.cos(j/2)) * MAX_HEIGHT * (1.5 - dist/GRID_SIZE)
            if Z[i,j] < 0: Z[i,j] = 0
            
    return X, Y, Z

# 2. THE RENDERER (SIMULATING LIGHT)
def render_prism():
    X, Y, Z = generate_crystal_lattice()
    
    # Setup the "Studio" (Dark Mode Void)
    fig = plt.figure(figsize=(10, 10), facecolor='#0d1117')
    ax = fig.add_subplot(111, projection='3d', facecolor='#0d1117')
    
    # Remove all axes (Floating in space)
    ax.axis('off')
    ax.grid(False)
    
    # Custom Lighting Logic (The "Shader")
    # We create a surface that looks like glowing liquid glass
    my_cmap = LinearSegmentedColormap.from_list("cyber", COLORS)
    
    # Render the Surface
    # alpha=0.9 gives the "Glass" effect
    # antialiased=True makes it sharp
    surf = ax.plot_surface(X, Y, Z, cmap=my_cmap, 
                           linewidth=0.2, edgecolors='#00fff5', alpha=0.85,
                           rstride=1, cstride=1, shade=True)
    
    # Add "Cyber" Lighting
    # A mix of ambient glow and directional neon light
    ax.view_init(elev=35, azim=-45) # The "Hero" Camera Angle
    
    # The "Floor" Reflection (Mirror Effect)
    # We plot a second inverted surface to simulate reflection on a black floor
    ax.plot_surface(X, Y, -Z*0.2, cmap='Greys', alpha=0.1)

    # 3. SAVE THE MASTERPIECE
    plt.tight_layout()
    plt.savefig('assets/prism_render.png', dpi=150, facecolor='#0d1117', bbox_inches='tight', pad_inches=0)
    print("Crystal Structure Crystallized.")

if __name__ == "__main__":
    render_prism()
