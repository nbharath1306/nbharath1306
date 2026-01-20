import json
import math
import random

WIDTH = 800
HEIGHT = 450 # 16:9 Cinematic Aspect Ratio

def generate_orbits():
    with open('survey_data.json', 'r') as f:
        planets = json.load(f)
    
    # Sort planets by mass (Heaviest closest to the sun)
    planets.sort(key=lambda x: x['mass'], reverse=True)
    
    # Limit to top 10 planets to avoid clutter (The Core System)
    core_system = planets[:10]
    
    simulated_universe = []
    
    center_x = WIDTH // 2
    center_y = HEIGHT // 2
    
    current_orbit_radius = 60
    
    for planet in core_system:
        # Calculate Orbital Mechanics
        current_orbit_radius += (planet['mass'] * 1.5) + 15
        
        # Generate random angle for current position
        angle = random.uniform(0, 6.28)
        
        x = center_x + math.cos(angle) * current_orbit_radius
        y = center_y + math.sin(angle) * current_orbit_radius
        
        simulated_universe.append({
            "name": planet['name'],
            "color": planet['color'],
            "radius": planet['mass'],
            "orbit_dist": current_orbit_radius,
            "x": x,
            "y": y,
            "stars": planet['stars']
        })
        
    with open('universe_state.json', 'w') as f:
        json.dump(simulated_universe, f, indent=2)
    print("ORBITAL MECHANICS CALCULATED.")

if __name__ == "__main__":
    generate_orbits()
