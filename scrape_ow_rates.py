import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time

def parse_hero_stats(html_content):
    """Parse hero statistics from HTML"""
    soup = BeautifulSoup(html_content, 'html.parser')
    heroes = []
    
    # Get all text content
    text = soup.get_text()
    
    # Split into lines and clean
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    print(f"Total lines found: {len(lines)}")
    
    # Debug: Print first 50 lines to see structure
    print("\n--- First 50 lines of content ---")
    for i, line in enumerate(lines[:50]):
        print(f"{i}: {line}")
    print("--- End of debug output ---\n")
    
    # Find the data section - look for "HeroPick RateWin Rate"
    try:
        start_idx = None
        
        # Try to find the header in different ways
        for i, line in enumerate(lines):
            # Check if line contains all three keywords
            if 'Hero' in line and 'Pick' in line and 'Win' in line:
                print(f"Found potential header at line {i}: {line}")
                start_idx = i + 1
                break
        
        if start_idx is None:
            # Try looking for just "Hero" followed by percentages
            for i, line in enumerate(lines):
                if line == 'Hero':
                    # Check if next few lines look like data
                    if i + 3 < len(lines) and '%' in lines[i + 2]:
                        print(f"Found 'Hero' at line {i}, assuming data starts after")
                        start_idx = i + 1
                        break
        
        if start_idx is None:
            print("ERROR: Could not find start of hero data")
            print("Searched for: 'Hero', 'Pick', 'Win' keywords")
            return heroes
        
        print(f"Data starts at line {start_idx}")
        
        # Find where data ends
        end_idx = len(lines)
        end_markers = [
            'Frequently Asked Questions',
            'What patch is',
            'The future is worth'
        ]
        
        for i in range(start_idx, len(lines)):
            for marker in end_markers:
                if marker in lines[i]:
                    end_idx = i
                    print(f"Found end marker '{marker}' at line {i}")
                    break
            if end_idx < len(lines):
                break
        
        print(f"Data ends at line {end_idx}")
        
        # Extract hero data
        hero_lines = lines[start_idx:end_idx]
        print(f"\nProcessing {len(hero_lines)} lines of hero data...")
        
        # Show sample of hero lines
        print(f"Sample hero lines:")
        for i in range(min(15, len(hero_lines))):
            print(f"  {i}: {hero_lines[i]}")
        
        # Parse in groups of 3: name, pick rate, win rate
        i = 0
        while i < len(hero_lines) - 2:
            name = hero_lines[i]
            pick = hero_lines[i + 1]
            win = hero_lines[i + 2]
            
            # Check if this looks like valid hero data
            if '%' in pick and '%' in win:
                heroes.append({
                    'name': name,
                    'pickRate': pick,
                    'winRate': win
                })
                print(f"  Added: {name} | {pick} | {win}")
                i += 3
            else:
                i += 1
        
        print(f"\nSuccessfully parsed {len(heroes)} heroes")
        
    except Exception as e:
        print(f"ERROR parsing hero data: {e}")
        import traceback
        traceback.print_exc()
    
    return heroes

def filter_heroes_by_role(heroes, role):
    """Filter heroes by their actual role"""
    
    TANK_HEROES = [
        'D.Va', 'Doomfist', 'Domina', 'Hazard', 'Junker Queen', 'Mauga', 
        'Orisa', 'Ramattra', 'Reinhardt', 'Roadhog', 'Sigma', 
        'Winston', 'Wrecking Ball', 'Zarya'
    ]
    
    DAMAGE_HEROES = [
        'Anran', 'Ashe', 'Bastion', 'Cassidy', 'Echo', 'Emre', 'Genji', 
        'Hanzo', 'Junkrat', 'Mei', 'Pharah', 'Reaper', 'Sojourn', 
        'Soldier: 76', 'Sombra', 'Symmetra', 'Torbjörn', 'Tracer', 
        'Vendetta', 'Venture', 'Widowmaker'
    ]
    
    SUPPORT_HEROES = [
        'Ana', 'Baptiste', 'Brigitte', 'Freja', 'Illari', 'Jetpack Cat', 
        'Juno', 'Kiriko', 'Lifeweaver', 'Lúcio', 'Mercy', 'Mizuki', 
        'Moira', 'Wuyang', 'Zenyatta'
    ]
    
    if role == 'Tank':
        filtered = [h for h in heroes if h['name'] in TANK_HEROES]
    elif role == 'Damage':
        filtered = [h for h in heroes if h['name'] in DAMAGE_HEROES]
    elif role == 'Support':
        filtered = [h for h in heroes if h['name'] in SUPPORT_HEROES]
    else:
        return heroes
    
    print(f"Filtered {len(heroes)} heroes to {len(filtered)} {role} heroes")
    return filtered

def scrape_all_heroes(region='Europe'):
    """Scrape all hero statistics"""
    
    url = f"https://overwatch.blizzard.com/en-us/rates/?input=PC&map=all-maps&region={region}&role=All&rq=2&tier=All"
    
    print(f"\nFetching data from Blizzard...")
    print(f"URL: {url}\n")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        print(f"HTTP Status: {response.status_code}")
        print(f"Content length: {len(response.content)} bytes")
        
        if response.status_code == 200:
            heroes = parse_hero_stats(response.content)
            return heroes
        else:
            print(f"❌ Failed: HTTP {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []

def main():
    print("=" * 70)
    print("Overwatch Stats Scraper - DEBUG MODE")
    print("=" * 70)
    
    # Scrape all heroes
    all_heroes = scrape_all_heroes()
    
    if not all_heroes:
        print("\n" + "=" * 70)
        print("❌ FAILED - No heroes scraped")
        print("=" * 70)
        exit(1)
    
    # Build final data structure
    data = {
        'lastUpdated': datetime.now().isoformat(),
        'source': 'Blizzard Entertainment Official Stats',
        'region': 'Europe',
        'tier': 'All Tiers',
        'gameMode': 'Competitive - Role Queue',
        'platform': 'PC (Mouse & Keyboard)',
        'disclaimer': 'Not affiliated with or endorsed by Blizzard Entertainment',
        'roles': {
            'Tank': filter_heroes_by_role(all_heroes, 'Tank'),
            'Damage': filter_heroes_by_role(all_heroes, 'Damage'),
            'Support': filter_heroes_by_role(all_heroes, 'Support'),
        }
    }
    
    # Calculate totals
    total = sum(len(heroes) for heroes in data['roles'].values())
    
    # Save to JSON
    with open('ow_rates.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print("\n" + "=" * 70)
    print(f"✅ SUCCESS! Scraped {total} heroes")
    print(f"   Tank: {len(data['roles']['Tank'])} heroes")
    print(f"   Damage: {len(data['roles']['Damage'])} heroes")
    print(f"   Support: {len(data['roles']['Support'])} heroes")
    print("📄 Saved to ow_rates.json")
    print("=" * 70)

if __name__ == '__main__':
    main()
