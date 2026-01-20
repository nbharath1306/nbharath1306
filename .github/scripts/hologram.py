import json
import datetime

def render_svg():
    with open('universe_state.json', 'r') as f:
        system = json.load(f)
        
    timestamp = datetime.datetime.now().strftime("%Y.%m.%d :: %H%M")
    
    # SVG HEADER
    svg = f'''<svg width="800" height="450" xmlns="http://www.w3.org/2000/svg">
    <style>
        .orbit {{ fill: none; stroke: #30363d; stroke-width: 1; opacity: 0.5; }}
        .planet {{ filter: drop-shadow(0 0 5px rgba(255,255,255,0.3)); }}
        .text {{ font-family: 'Courier New', monospace; fill: #8b949e; font-size: 10px; }}
        .title {{ font-family: sans-serif; fill: white; font-weight: bold; font-size: 24px; letter-spacing: 4px; }}
        .hud-line {{ stroke: #00ffff; stroke-width: 1; opacity: 0.3; }}
        
        /* ANIMATIONS */
        @keyframes pulse {{ 0% {{ r: 25; opacity: 0.8; }} 50% {{ r: 30; opacity: 0.4; }} 100% {{ r: 25; opacity: 0.8; }} }}
        .sun {{ animation: pulse 4s infinite; }}
    </style>
    
    <rect width="100%" height="100%" fill="#0d1117" />
    
    <line x1="50" y1="50" x2="50" y2="400" class="hud-line" />
    <line x1="50" y1="400" x2="750" y2="400" class="hud-line" />
    <text x="60" y="390" class="text">SYS_TIME: {timestamp}</text>
    <text x="60" y="375" class="text">SECTOR: N_BHARATH_PRIME</text>
    
    <circle cx="400" cy="225" r="25" fill="url(#grad1)" class="sun" />
    <defs>
        <radialGradient id="grad1" cx="50%" cy="50%" r="50%" fx="50%" fy="50%">
            <stop offset="0%" style="stop-color:white;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#00ffff;stop-opacity:1" />
        </radialGradient>
    </defs>
    '''
    
    # RENDER PLANETS AND ORBITS
    for p in system:
        # Draw Orbit Ring
        svg += f'<circle cx="400" cy="225" r="{p["orbit_dist"]}" class="orbit" />\n'
        
        # Draw Planet
        svg += f'<circle cx="{p["x"]}" cy="{p["y"]}" r="{p["radius"]}" fill="{p["color"]}" class="planet" />\n'
        
        # Draw Label (Only if large enough)
        if p['radius'] > 10:
            svg += f'<text x="{p["x"] + 15}" y="{p["y"] + 5}" class="text" fill="white">{p["name"].upper()}</text>\n'
            
    # CLOSE SVG
    svg += '''
    <text x="400" y="40" text-anchor="middle" class="title">SYSTEM SINGULARITY</text>
    </svg>'''
    
    with open('assets/singularity_map.svg', 'w') as f:
        f.write(svg)
    print("HOLOGRAM PROJECTION COMPLETE.")

if __name__ == "__main__":
    render_svg()
