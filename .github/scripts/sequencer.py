"""
PROJECT PROMETHEUS: BIO-DIGITAL SEQUENCER
Author: N_BHARATH (System Architect)
Version: 1.0.0 (Genesis)

Architecture:
1. DataFetcher: Retreives genomic payload (GitHub Data).
2. Engine3D: Calculates helical projection & molecular occlusion.
3. Renderer: Synthesizes high-fidelity GIF output with depth-buffering.
"""

import os
import json
import math
import urllib.request
import urllib.error
from datetime import datetime

# Check if PIL is available, if not, we gracefully degrade (or fail if critical)
# In GitHub Actions, we install it.
try:
    from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
except ImportError:
    print("CRITICAL SYSTEM FAILURE: Pillow library missing. Install via pip.")
    exit(1)

# --- CONSTANTS & CONFIGURATION ---
CONFIG = {
    "username": "nbharath1306",
    "resolution": (800, 600),
    "frames": 60,
    "focal_length": 600,
    "atom_base_radius": 6,     # Base size for atoms
    "helix_radius": 150,       # Radius of the DNA spiral
    "helix_height": 550,       # Total height of the segment
    "turns": 2.5,              # Number of full twists
    "bg_color": "#0d1117",     # GitHub Dark Dimmed
    "bond_color": (0, 243, 255), # Cyan bonds
}

# --- ATOM VISUALIZATION PROTOCOLS ---
# Extended palette for languages
PALETTE = {
    "start": "#00f3ff", # Cyan
    "end":   "#bd00ff", # Electric Purple
    "Python": (53, 114, 165),
    "JavaScript": (241, 224, 90),
    "TypeScript": (43, 116, 137),
    "HTML": (227, 76, 38),
    "CSS": (86, 61, 124),
    "Java": (176, 114, 25),
    "Go": (0, 173, 216),
    "Rust": (222, 165, 132),
    "C": (85, 85, 85),
    "C++": (243, 75, 125),
    "Unknown": (100, 100, 100) # Grey matter
}

class Atom:
    def __init__(self, x, y, z, color, size, is_backbone=False):
        self.x = x
        self.y = y
        self.z = z
        self.color = color
        self.size = size
        self.is_backbone = is_backbone
        # Computed during projection
        self.proj_x = 0
        self.proj_y = 0
        self.scale = 0
        self.z_index = 0

class DataFetcher:
    """Retrieves and processes GitHub repository data."""
    
    @staticmethod
    def fetch_repos(username):
        print(f">> INITIALIZING DATALINK: {username}")
        url = f"https://api.github.com/users/{username}/repos?sort=updated&per_page=40&type=owner"
        repos = []
        try:
            req = urllib.request.Request(url)
            # Add headers if we have a token, otherwise rate limits might apply
            # But standard runs should be fine for public data
            if os.environ.get("GITHUB_TOKEN"):
                req.add_header("Authorization", f"Bearer {os.environ.get('GITHUB_TOKEN')}")
            
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                for repo in data:
                    repos.append({
                        "name": repo["name"],
                        "language": repo["language"] or "Unknown",
                        "size": repo["size"]
                    })
        except urllib.error.URLError as e:
            print(f"!! CONNECTION ERROR: {e}")
            # Fallback mock data
            for i in range(40):
                repos.append({"name": f"Mock-{i}", "language": "Unknown", "size": 1000})
        
        # Determine max size for normalization
        max_size = max([r["size"] for r in repos]) if repos else 100
        
        # Inject normalized radius
        for r in repos:
            # Logarithmic scaling for size to avoid massive atoms
            # Base size 6, plus up to 8 based on log of size
            import math
            size_bonus = math.log(r["size"] + 1) if r["size"] > 0 else 0
            # Cap bonus
            size_bonus = min(size_bonus, 12)
            r["radius"] = CONFIG["atom_base_radius"] + (size_bonus * 0.5)

        # Pad if short
        while len(repos) < 40:
            repos.append({
                "name": "Null-Void",
                "language": "Unknown",
                "radius": CONFIG["atom_base_radius"],
                "color": PALETTE["Unknown"]
            })
            
        print(f">> DATA ACQUIRED: {len(repos)} packets")
        return repos[:40] # Strict limit

class Engine3D:
    """The Math Kernel: Handles 3D transformations."""
    
    @staticmethod
    def generate_helix(repos):
        atoms = []
        count = len(repos)
        
        # We need two strands.
        # Repos are mapped to the primary strand.
        # Complementary strand is procedural.
        
        for i, repo in enumerate(repos):
            # Calculate position along the helix
            # t goes from -1 to 1 based on height
            t = i / (count - 1)
            y = (t - 0.5) * CONFIG["helix_height"]
            
            # Angle for the spiral
            theta = t * CONFIG["turns"] * 2 * math.pi
            
            # Strand A (Repositories)
            radius = CONFIG["helix_radius"] 
            x_a = radius * math.cos(theta)
            z_a = radius * math.sin(theta)
            
            # Strand B (Complementary - offset by PI)
            x_b = radius * math.cos(theta + math.pi)
            z_b = radius * math.sin(theta + math.pi)
            
            # Resolve Color
            lang_color = PALETTE.get(repo["language"], PALETTE["Unknown"])
            if isinstance(lang_color, str) and lang_color.startswith("#"):
                 # Convert hex to rgb
                 lang_color = tuple(int(lang_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
            
            # Atom A (Repo)
            atoms.append(Atom(x_a, y, z_a, lang_color, repo["radius"], is_backbone=False))
            
            # Atom B (Backbone/Complement)
            # Make it a uniform color or complimentary
            comp_color = (100, 255, 218) # Tealish
            atoms.append(Atom(x_b, y, z_b, comp_color, CONFIG["atom_base_radius"] * 0.8, is_backbone=True))
            
        return atoms

    @staticmethod
    def rotate_point(x, z, angle):
        """Applies Y-axis rotation matrix."""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        new_x = x * cos_a - z * sin_a
        new_z = x * sin_a + z * cos_a
        return new_x, new_z

    @staticmethod
    def project(atoms, angle_y):
        """Projects 3D atoms to 2D space with rotation."""
        projected = []
        width, height = CONFIG["resolution"]
        cx, cy = width / 2, height / 2
        f = CONFIG["focal_length"]
        
        for i in range(0, len(atoms), 2):
            # Process pairs to manage bonds easily in rendering if needed,
            # but for Painter's algo, we simplify: project all, then sort.
            pass

        for atom in atoms:
            # 1. Rotate
            rot_x, rot_z = Engine3D.rotate_point(atom.x, atom.z, angle_y)
            
            # 2. Translate Z (push back so camera doesn't clip)
            # Camera is at z = -f usually, or object is at z.
            # Let's say camera is at -1000.
            # Simple perspective projection:
            # scale = f / (f + z) 
            # We shift z so it's always positive relative to camera
            z_camera_offset = 400
            scale = f / (f + (rot_z + z_camera_offset))
            
            proj_x = rot_x * scale + cx
            proj_y = atom.y * scale + cy
            
            atom.proj_x = proj_x
            atom.proj_y = proj_y
            atom.scale = scale
            atom.z_index = rot_z # Store for sorting
            
        return atoms

class Renderer:
    """The Visualization Pipeline."""
    
    @staticmethod
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    @staticmethod
    def draw_frame(atoms, frame_idx):
        # Setup Canvas
        img = Image.new("RGBA", CONFIG["resolution"], CONFIG["bg_color"])
        draw = ImageDraw.Draw(img)
        
        # Sort atoms by Z (Painter's Algorithm)
        # Deepest Z (furthest) drawn first. 
        # In our coord system assuming z+ is away or towards?
        # rotated z: +z is usually front in this math, let's check.
        # If we pushed +z as "depth", then larger Z is further.
        # Let's assume standard right hand rule, rotated.
        # We want to draw FAR objects first. 
        # Z-sorting: sort ascending or descending?
        # If scale = 1 / (z_dist), larger z_dist means smaller/further.
        # We stored rot_z. If rot_z is +ve, it came closer or further?
        # rot_z was added to offset. larger (rot_z + offset) -> smaller scale -> further away.
        # So high z-index = far away. Sort descending.
        
        atoms.sort(key=lambda a: a.z_index, reverse=True)
        
        # We need to draw bonds between pairs. 
        # Since we sorted atoms, we lost the pairing structure.
        # Strategy: Draw bonds first? No, bonds must occlude correctly too.
        # Better: Treat bonds as objects? Too complex for this script.
        # Compromise: Draw bonds between paired atoms if BOTH are behind... 
        # Actually, simpler Bio-Cyberpunk aesthetic:
        # Draw connectivity lines first (behind everything)?
        # Or iterate pairs and calculate individual z-depth for the bond.
        
        # Let's reconstruct pairs just for bond calculation
        # The atoms list has pairs at indices i and i+1 in the unsorted list...
        # But we sorted them.
        # Let's keep a reference?
        # Alternative: The pairs are inherently index i and i+1 in the `generate_helix` output.
        # Let's modify the sort to handle drawing order but keeping knowledge.
        # Actually, let's just pre-calculate bonds as drawable primitives.
        
        drawable_objects = []
        
        # Helper to find paired atom in the sorted list? No.
        # Let's separate "Project" phase from "Sort" phase properly.
        # We have the original list.
        
        pass 
        
    @staticmethod
    def render(repos):
        print(f">> ENGAGING RENDER CORE: {CONFIG['frames']} frames @ {CONFIG['resolution']}")
        frames = []
        
        # 1. Generate Geometry
        raw_atoms = Engine3D.generate_helix(repos)
        
        # 2. Render Loop
        for f in range(CONFIG["frames"]):
            # Angle: 0 to 2*PI
            angle = (f / CONFIG["frames"]) * 2 * math.pi
            
            # Deep copy or reset atoms?
            # We modify atoms in place in `project`, so we need to be careful.
            # Actually `project` overwrites proj_x/y. 
            # We can reuse the same instances if we don't need history.
            
            Engine3D.project(raw_atoms, angle)
            
            # Create Frame
            img = Image.new("RGB", CONFIG["resolution"], CONFIG["bg_color"])
            draw = ImageDraw.Draw(img)
            
            # Z-Sorting for Painter's
            # We need to distinguish between atoms and bonds.
            # Let's create a display list.
            display_list = []
            
            # Create Bond primitives
            # Pairs are (0,1), (2,3)...
            for i in range(0, len(raw_atoms), 2):
                a1 = raw_atoms[i]
                a2 = raw_atoms[i+1]
                
                # Bond Z is average
                bond_z = (a1.z_index + a2.z_index) / 2
                display_list.append({
                    "type": "bond",
                    "z": bond_z,
                    "obj": (a1, a2)
                })
                
                # Add atoms
                display_list.append({"type": "atom", "z": a1.z_index, "obj": a1})
                display_list.append({"type": "atom", "z": a2.z_index, "obj": a2})
            
            # Sort: Furthest (highest Z) first
            display_list.sort(key=lambda item: item["z"], reverse=True)
            
            # Draw
            for item in display_list:
                z_val = item["z"]
                # Depth Dimming
                # Normalize z range slightly for alpha/brightness
                # z varies roughly from -150 to 150 (radius)
                # Map to brightness 0.3 to 1.0
                depth_factor = (z_val + 200) / 400 
                depth_factor = max(0.2, min(1.0, 1.0 - depth_factor)) # Further (high z) = darker?
                # Wait, z_camera_offset was +400. 
                # scale = f / (f + z). Large z -> small scale -> Far.
                # So Large Z = Far.
                # Brightness should be lower for Large Z.
                # depth_factor = 1.0 - (normalized_z)
                
                brightness = max(0.3, 1.0 - ((z_val + 150) / 300))
                
                if item["type"] == "bond":
                    a1, a2 = item["obj"]
                    # Draw Line
                    # Color with depth dimming
                    base_c = CONFIG["bond_color"]
                    final_c = (
                        int(base_c[0] * brightness),
                        int(base_c[1] * brightness),
                        int(base_c[2] * brightness)
                    )
                    draw.line([(a1.proj_x, a1.proj_y), (a2.proj_x, a2.proj_y)], fill=final_c, width=1)
                    
                    # Add "Rungs" markers? Or just the line. PRD says "dotted or tech look".
                    # Standard line is fine for minimal dependency.
                    
                elif item["type"] == "atom":
                    atom = item["obj"]
                    r = atom.size * atom.scale
                    
                    # Color processing
                    c = atom.color
                    final_c = (
                        int(c[0] * brightness),
                        int(c[1] * brightness),
                        int(c[2] * brightness)
                    )
                    
                    # Draw
                    x, y = atom.proj_x, atom.proj_y
                    bbox = [x - r, y - r, x + r, y + r]
                    
                    # Glow effect for high-tech look (Simulated by layered circles)
                    if atom.size > CONFIG["atom_base_radius"] * 1.2:
                        # Draw halo
                        halo_r = r * 1.5
                        halo_bbox = [x - halo_r, y - halo_r, x + halo_r, y + halo_r]
                        # PIL doesn't support alpha on draw.ellipse directly on RGB image easily without mask
                        # Simulating glow with outline or darker shade
                        draw.ellipse(halo_bbox, outline=final_c, width=1)
                        
                    draw.ellipse(bbox, fill=final_c)
            
            # Post-Process: Glow/Bloom (Optional, expensive/unsupported in basic PIL without numpy often)
            # Keeping it simple for speed.
            
            frames.append(img)
            
        # Save GIF
        print(f">> COMPILING SEQUENCE: {len(frames)} frames")
        frames[0].save(
            "assets/dna.gif",
            save_all=True,
            append_images=frames[1:],
            duration=1000/60, # 60 FPS target implies ~16ms, but GIFs cap around 50fps usually. 20ms is safe.
            loop=0
        )
        print(">> SEQUENCE ARCHIVED: assets/dna.gif")

if __name__ == "__main__":
    print(">> PROJECT PROMETHEUS BIOS // SYSTEM STARTUP")
    
    # 1. Fetch
    repo_data = DataFetcher.fetch_repos(CONFIG["username"])
    
    # 2. Render
    Renderer.render(repo_data)
    
    print(">> SYSTEM SHUTDOWN // UPLOAD READY")
