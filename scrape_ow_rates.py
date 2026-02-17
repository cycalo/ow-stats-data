import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time
import re

def parse_hero_stats(html_content):
    """Parse hero statistics from HTML"""
    soup = BeautifulSoup(html_content, 'html.parser')
    heroes = []
    
    # Get all text content
    text = soup.get_text()
    
    # Split into lines and clean
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Find the data section
    try:
        # Look for the table header
        start_idx = None
        for i, line in enumerate(lines):
            if 'HeroPick RateWin Rate' in line or line == 'HeroPick RateWin Rate':
                start_idx = i + 1
                break
        
        if start_idx is None:
            print("Could not find 'HeroPick RateWin Rate' header")
            return heroes
        
        # Find where hero data ends (FAQ section)
        end_idx = len(lines)
        end_markers = [
            'Frequently Asked Questions',
            'What patch is this data from?',
            'The future is worth fighting for'
        ]
        
        for marker in end_markers:
            for i in range(start_idx, len(lines)):
                if marker in lines[i]:
                    end_idx = min(end_idx, i)
                    break
        
        # Extract hero data (groups of 3: name, pick rate, win rate)
        hero_lines = lines[start_idx:end_idx]
        
        print(f"Found {len(hero_lines)} lines of data between indices {start_idx} and {end_idx}")
        
        i = 0
        while i < len(hero_lines) - 2:
            name = hero_lines[i]
            pick = hero_lines[i + 1]
            win = hero_lines[i + 2]
            
            # Validate this is hero data (both should have %)
            if '%' in pick and '%' in win:
                heroes.append({
                    'name': name,
                    'pickRate': pick,
                    'winRate': win
                })
                i += 3
            else:
                # Not valid hero data, skip this line
                i += 1
        
        print(f"Successfully parsed {len(heroes)} heroes")
        
    except Exception as e:
        print(f"Error parsing hero data: {e}")
    
    return heroes

def scrape_role(role, region='Europe'):
    """Scrape statistics for a specific role"""
    
    # Note: Blizzard's page shows ALL heroes regardless of role filter
    # The role filter just highlights them in the UI but returns all data
    # So we'll scrape with role=All and filter client-side
    
    url = f"https://overwatch.blizzard.com/en-us/rates/?input=PC&map=all-maps&region={region}&role={role}&rq=2&tier=All"
    
    print(f"\nScraping {role} heroes from {region}...")
    print(f"URL: {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            heroes = parse_hero_stats(response.content)
            
            # Filter by role if not "All"
            if role != 'All':
                heroes = filter_heroes_by_role(heroes, role)
            
            print(f"✅ Found {len(heroes)} {role} heroes")
            return heroes
        else:
            print(f"❌ Failed: HTTP {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Error scraping {role}: {e}")
        return []

def filter_heroes_by_role(heroes, role):
    """Filter heroes by their actual role"""
    
    # Define hero roles (based on Overwatch 2 roster)
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
        return [h for h in heroes if h['name'] in TANK_HEROES]
    elif role == 'Damage':
        return [h for h in heroes if h['name'] in DAMAGE_HEROES]
    elif role == 'Support':
        return [h for h in heroes if h['name'] in SUPPORT_HEROES]
    else:
        return heroes

def main():
    print("=" * 60)
    print("Overwatch Stats Scraper")
    print("=" * 60)
    
    data = {
        'lastUpdated': datetime.now().isoformat(),
        'source': 'Blizzard Entertainment Official Stats',
        'region': 'Europe',
        'tier': 'All Tiers',
        'gameMode': 'Competitive - Role Queue',
        'platform': 'PC (Mouse & Keyboard)',
        'disclaimer': 'Not affiliated with or endorsed by Blizzard Entertainment',
        'roles': {}
    }
    
    # Scrape all heroes once (they're all on the same page)
    print("\nFetching hero data...")
    all_heroes = scrape_role('All')
    
    if not all_heroes:
        print("\n❌ Failed to scrape any heroes!")
        print("Check if Blizzard's page structure has changed.")
        exit(1)
    
    # Filter by role
    data['roles']['Tank'] = filter_heroes_by_role(all_heroes, 'Tank')
    data['roles']['Damage'] = filter_heroes_by_role(all_heroes, 'Damage')
    data['roles']['Support'] = filter_heroes_by_role(all_heroes, 'Support')
    
    # Calculate totals
    total_heroes = sum(len(heroes) for heroes in data['roles'].values())
    
    # Save to JSON
    with open('ow_rates.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print("\n" + "=" * 60)
    print(f"✅ SUCCESS! Scraped {total_heroes} heroes")
    print(f"   Tank: {len(data['roles']['Tank'])} heroes")
    print(f"   Damage: {len(data['roles']['Damage'])} heroes")
    print(f"   Support: {len(data['roles']['Support'])} heroes")
    print("📄 Saved to ow_rates.json")
    print("=" * 60)

if __name__ == '__main__':
    main()
