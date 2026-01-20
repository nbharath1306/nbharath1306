import os
import json
import urllib.request

# CONFIGURATION
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
USER = "nbharath1306" # YOUR USERNAME

def get_repos():
    url = f"https://api.github.com/users/{USER}/repos?per_page=100&sort=updated"
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'token {GITHUB_TOKEN}')
    
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data
    except Exception as e:
        print(f"CRITICAL FAILURE IN SURVEYOR: {e}")
        return []

def analyze_cosmos():
    raw_repos = get_repos()
    
    celestial_bodies = []
    
    for repo in raw_repos:
        # Determine Planet Type based on Language
        lang = repo.get('language', 'Unknown')
        planet_type = "Rocky"
        color = "#8b949e" # Default Grey
        
        if lang == "Python": color = "#3572A5"; planet_type = "Gas Giant"
        elif lang == "JavaScript": color = "#f1e05a"; planet_type = "Desert"
        elif lang == "TypeScript": color = "#2b7489"; planet_type = "Ocean"
        elif lang == "HTML": color = "#e34c26"; planet_type = "Molten"
        elif lang == "Java": color = "#b07219"; planet_type = "Terrestrial"
        
        # Calculate Mass based on Size
        mass = repo.get('size', 100) / 1000
        if mass > 50: mass = 50 # Cap size
        if mass < 5: mass = 5
        
        celestial_bodies.append({
            "name": repo['name'],
            "type": planet_type,
            "color": color,
            "mass": mass,
            "stars": repo['stargazers_count'],
            "last_active": repo['updated_at']
        })
        
    # Save the Survey Data
    with open('survey_data.json', 'w') as f:
        json.dump(celestial_bodies, f, indent=2)
    print(f"SURVEY COMPLETE. DISCOVERED {len(celestial_bodies)} WORLDS.")

if __name__ == "__main__":
    analyze_cosmos()
