"""
PROJECT DYSON: 3D DYSON SPHERE ENGINE
Architect: N_BHARATH
Simulation: Fibonacci Sphere Distribution + Billboard Rendering
Visual: Type II Civilization Mega-Structure

Overview:
Renders a rotating 3D Dyson Sphere where each hexagonal panel represents a repository.
Uses Fibonacci point distribution for even panel placement.
Lighting includes rim glow, core bloom, and chromatic aberration.
"""

import os
import json
import math
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from typing import List, Tuple, Dict

try:
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
except ImportError:
    print("CRITICAL: NumPy or Pillow missing. Install via pip.")
    exit(1)

# --- CONFIGURATION ---
CONFIG = {
    "username": "nbharath1306",
    "width": 800,
    "height": 600,
    "sphere_radius": 180,
    "panel_count": 120,  # Fibonacci points
    "total_frames": 60,
    "fps": 30,
    "bg_color": (13, 17, 23),  # #0d1117
    "core_color": (255, 200, 50),  # Golden star core
    "panel_base_color": (40, 50, 70),  # Dark metallic
    "panel_active_color": (80, 180, 255),  # Cyan glow
    "gap_color": (0, 243, 255),  # Neon cyan veins
}

# Language color palette
LANG_COLORS = {
    "Python": (53, 114, 165),
    "JavaScript": (241, 224, 90),
    "TypeScript": (43, 116, 137),
    "Go": (0, 173, 216),
    "Rust": (222, 165, 132),
    "Java": (176, 114, 25),
    "C++": (243, 75, 125),
    "HTML": (227, 76, 38),
    "CSS": (86, 61, 124),
    "Unknown": (100, 100, 100),
}


class EnergyHarvester:
    """Data Layer: Fetches GitHub metrics."""
    
    @staticmethod
    def fetch_data(username: str) -> Dict:
        """Fetches repos and calculates energy metrics."""
        print(f">> HARVESTING ENERGY FROM: {username}")
        
        url = f"https://api.github.com/users/{username}/repos?sort=updated&per_page=50&type=owner"
        repos = []
        total_stars = 0
        total_size = 0
        
        try:
            req = urllib.request.Request(url)
            if os.environ.get("GITHUB_TOKEN"):
                req.add_header("Authorization", f"Bearer {os.environ.get('GITHUB_TOKEN')}")
            
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                for repo in data:
                    repos.append({
                        "name": repo["name"],
                        "language": repo["language"] or "Unknown",
                        "stars": repo["stargazers_count"],
                        "size": repo["size"],
                        "updated": repo["updated_at"],
                        "archived": repo.get("archived", False),
                    })
                    total_stars += repo["stargazers_count"]
                    total_size += repo["size"]
        except urllib.error.URLError as e:
            print(f"   ! CONNECTION ERROR: {e}")
            # Mock data fallback
            for i in range(50):
                repos.append({
                    "name": f"Repo-{i}",
                    "language": list(LANG_COLORS.keys())[i % len(LANG_COLORS)],
                    "stars": i * 2,
                    "size": 1000,
                    "updated": datetime.now().isoformat(),
                    "archived": False,
                })
            total_stars = 100
            total_size = 50000
        
        # Calculate momentum (recent activity)
        # Count repos updated in last 7 days
        recent_count = 0
        now = datetime.now()
        for repo in repos:
            try:
                updated = datetime.fromisoformat(repo["updated"].replace("Z", "+00:00"))
                if (now - updated.replace(tzinfo=None)).days < 7:
                    recent_count += 1
            except:
                pass
        
        metrics = {
            "repos": repos[:CONFIG["panel_count"]],
            "total_stars": total_stars,
            "total_size": total_size,
            "momentum": recent_count,
            "luminosity": min(1.0, total_stars / 200),  # Normalize to 0-1
            "rotation_speed": 0.5 + (recent_count / 20),  # Base speed + activity bonus
        }
        
        print(f"   Stars: {total_stars} | Size: {total_size}KB | Momentum: {recent_count} repos")
        return metrics


class Panel:
    """Represents a single hexagonal panel on the sphere."""
    
    def __init__(self, x: float, y: float, z: float, index: int):
        self.pos = np.array([x, y, z])
        self.index = index
        self.color = CONFIG["panel_base_color"]
        self.is_active = False
        self.language = "Unknown"
        self.glow_intensity = 0.0
    
    def set_repo_data(self, repo: Dict):
        """Assigns repository data to this panel."""
        self.language = repo["language"]
        self.is_active = not repo["archived"] and repo["stars"] >= 0
        self.color = LANG_COLORS.get(repo["language"], LANG_COLORS["Unknown"])
        self.glow_intensity = min(1.0, repo["stars"] / 50)  # Brighter for more stars


class SphereTracer:
    """3D Engine: Generates Fibonacci sphere and handles projection."""
    
    def __init__(self, panel_count: int, radius: float):
        self.panel_count = panel_count
        self.radius = radius
        self.panels: List[Panel] = []
        self._generate_fibonacci_sphere()
    
    def _generate_fibonacci_sphere(self):
        """
        Uses Fibonacci lattice to evenly distribute points on a sphere.
        Golden ratio method for uniform distribution.
        """
        print(f">> CONSTRUCTING MEGA-STRUCTURE: {self.panel_count} panels")
        
        golden_ratio = (1 + math.sqrt(5)) / 2
        
        for i in range(self.panel_count):
            # Latitude (theta)
            theta = 2 * math.pi * i / golden_ratio
            
            # Longitude (phi) - arccos for even distribution
            phi = math.acos(1 - 2 * (i + 0.5) / self.panel_count)
            
            # Convert spherical to Cartesian
            x = self.radius * math.sin(phi) * math.cos(theta)
            y = self.radius * math.sin(phi) * math.sin(theta)
            z = self.radius * math.cos(phi)
            
            self.panels.append(Panel(x, y, z, i))
    
    def assign_repos(self, repos: List[Dict]):
        """Maps repositories to panels."""
        for i, panel in enumerate(self.panels):
            if i < len(repos):
                panel.set_repo_data(repos[i])
    
    @staticmethod
    def rotate_y(pos: np.ndarray, angle: float) -> np.ndarray:
        """Rotates point around Y-axis."""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        return np.array([
            pos[0] * cos_a + pos[2] * sin_a,
            pos[1],
            -pos[0] * sin_a + pos[2] * cos_a
        ])
    
    @staticmethod
    def rotate_x(pos: np.ndarray, angle: float) -> np.ndarray:
        """Rotates point around X-axis (for tilt)."""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        return np.array([
            pos[0],
            pos[1] * cos_a - pos[2] * sin_a,
            pos[1] * sin_a + pos[2] * cos_a
        ])
    
    def project(self, pos: np.ndarray, width: int, height: int) -> Tuple[float, float, float]:
        """Projects 3D point to 2D screen with perspective."""
        focal = 500
        z_offset = 400
        
        scale = focal / (focal + pos[2] + z_offset)
        x_2d = pos[0] * scale + width / 2
        y_2d = pos[1] * scale + height / 2
        
        return x_2d, y_2d, scale


class OrbitalForge:
    """Rendering Pipeline: Produces the final visualization."""
    
    @staticmethod
    def draw_hexagon(draw: ImageDraw.Draw, cx: float, cy: float, size: float, 
                     color: Tuple[int, int, int], outline_color: Tuple[int, int, int] = None):
        """Draws a hexagon at the given center."""
        points = []
        for i in range(6):
            angle = math.pi / 3 * i - math.pi / 6  # Flat-top hexagon
            px = cx + size * math.cos(angle)
            py = cy + size * math.sin(angle)
            points.append((px, py))
        
        draw.polygon(points, fill=color, outline=outline_color)
    
    @staticmethod
    def apply_bloom(img: Image.Image, intensity: float = 0.5) -> Image.Image:
        """Applies bloom effect by blurring bright areas."""
        # Extract bright areas
        bright = img.copy()
        enhancer = ImageEnhance.Brightness(bright)
        bright = enhancer.enhance(1.5)
        
        # Blur
        blurred = bright.filter(ImageFilter.GaussianBlur(radius=15))
        
        # Blend back
        return Image.blend(img, blurred, alpha=intensity * 0.4)
    
    @staticmethod
    def apply_chromatic_aberration(img: Image.Image, strength: int = 2) -> Image.Image:
        """Shifts R and B channels for cinematic effect."""
        r, g, b = img.split()
        
        # Shift red left, blue right
        r = r.transform(r.size, Image.Transform.AFFINE, (1, 0, -strength, 0, 1, 0))
        b = b.transform(b.size, Image.Transform.AFFINE, (1, 0, strength, 0, 1, 0))
        
        return Image.merge("RGB", (r, g, b))
    
    @staticmethod
    def render_frame(tracer: SphereTracer, metrics: Dict, frame: int, 
                     width: int, height: int) -> Image.Image:
        """Renders a single frame of the Dyson Sphere."""
        
        # Create canvas
        img = Image.new("RGB", (width, height), CONFIG["bg_color"])
        draw = ImageDraw.Draw(img)
        
        # Calculate rotation angle
        speed = metrics["rotation_speed"]
        angle_y = (frame / CONFIG["total_frames"]) * 2 * math.pi * speed
        angle_x = 0.3  # Slight tilt
        
        # Process panels
        panel_data = []
        
        for panel in tracer.panels:
            # Rotate
            rotated = SphereTracer.rotate_y(panel.pos, angle_y)
            rotated = SphereTracer.rotate_x(rotated, angle_x)
            
            # Project
            x_2d, y_2d, scale = tracer.project(rotated, width, height)
            
            # Calculate lighting
            # Fresnel (rim lighting) - brighter at edges
            z_norm = rotated[2] / tracer.radius
            fresnel = 1.0 - abs(z_norm)
            fresnel = fresnel ** 2  # More pronounced
            
            # Visibility (back-face culling approximation)
            visible = rotated[2] < tracer.radius * 0.8
            
            if visible:
                panel_data.append({
                    "x": x_2d,
                    "y": y_2d,
                    "z": rotated[2],
                    "scale": scale,
                    "fresnel": fresnel,
                    "panel": panel,
                })
        
        # Z-sort (back to front)
        panel_data.sort(key=lambda p: p["z"], reverse=True)
        
        # Draw core glow first (behind panels)
        cx, cy = width / 2, height / 2
        for radius_factor in [0.7, 0.5, 0.3]:
            glow_radius = int(tracer.radius * radius_factor)
            glow_alpha = int(50 * (1 - radius_factor) * metrics["luminosity"])
            glow_color = tuple(min(255, c + glow_alpha) for c in CONFIG["core_color"])
            draw.ellipse(
                [cx - glow_radius, cy - glow_radius, cx + glow_radius, cy + glow_radius],
                fill=glow_color
            )
        
        # Draw panels
        for pd in panel_data:
            panel = pd["panel"]
            x, y = pd["x"], pd["y"]
            scale = pd["scale"]
            fresnel = pd["fresnel"]
            
            # Calculate panel size
            base_size = 12
            size = base_size * scale
            
            # Calculate color with lighting
            base_color = panel.color if panel.is_active else CONFIG["panel_base_color"]
            
            # Apply fresnel (rim light)
            lit_color = tuple(
                int(min(255, c * (0.6 + 0.4 * fresnel) + fresnel * 60))
                for c in base_color
            )
            
            # Gap glow color
            gap_intensity = fresnel * 0.5 + panel.glow_intensity * 0.5
            gap_color = tuple(
                int(min(255, c * gap_intensity))
                for c in CONFIG["gap_color"]
            )
            
            # Draw hexagon
            OrbitalForge.draw_hexagon(draw, x, y, size, lit_color, gap_color)
        
        # Post-processing
        img = OrbitalForge.apply_bloom(img, metrics["luminosity"])
        img = OrbitalForge.apply_chromatic_aberration(img, 2)
        
        return img


def run_simulation():
    print(">> PROJECT DYSON: MEGA-STRUCTURE SIMULATION")
    print("=" * 50)
    
    # 1. Harvest Data
    metrics = EnergyHarvester.fetch_data(CONFIG["username"])
    
    # 2. Construct Sphere
    tracer = SphereTracer(CONFIG["panel_count"], CONFIG["sphere_radius"])
    tracer.assign_repos(metrics["repos"])
    
    # 3. Render Animation
    print(f">> FORGING ORBITAL STRUCTURE: {CONFIG['total_frames']} frames")
    frames = []
    
    for f in range(CONFIG["total_frames"]):
        frame = OrbitalForge.render_frame(
            tracer, metrics, f,
            CONFIG["width"], CONFIG["height"]
        )
        frames.append(frame)
        
        if f % 15 == 0:
            print(f"   Frame {f}/{CONFIG['total_frames']}")
    
    # 4. Save GIF
    print(">> COMPILING HOLOGRAPHIC PROJECTION...")
    duration = int(1000 / CONFIG["fps"])
    
    frames[0].save(
        "assets/dyson.gif",
        save_all=True,
        append_images=frames[1:],
        duration=duration,
        loop=0,
        optimize=False
    )
    
    print(">> ASSET SECURED: assets/dyson.gif")
    print(f">> POWER OUTPUT: {metrics['total_stars']} TW (Star-Units)")
    print(">> PROJECT DYSON: COMPLETE")


if __name__ == "__main__":
    run_simulation()
