import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re

def parse_hero_stats(html_content):
    """Parse hero statistics using regex from the concatenated text"""
    soup = BeautifulSoup(html_content, 'html.parser')
    heroes = []
    
    # Get all text content
    text = soup.get_text()
    
    print(f"Content length: {len(text)} characters")
    
    # Find the section between "HeroPick RateWin Rate" and "Frequently Asked Questions"
    hero_section_match = re.search(
        r'HeroPick RateWin Rate(.+?)Frequently Asked Questions',
        text,
        re.DOTALL
    )
    
    if not hero_section_match:
        print("ERROR: Could not find hero data section")
        return heroes
    
    hero_data = hero_section_match.group(1)
    print(f"Found hero data section: {len(hero_data)} characters")
    
    # Pattern: HeroName followed by two percentages
    pattern = r'([A-Za-z][A-Za-z\s:\.]+?)(\d+(?:\.\d+)?%)(\d+(?:\.\d+)?%)'
    
    matches = re.findall(pattern, hero_data)
    
    print(f"Found {len(matches)} potential hero entries")
    
    for match in matches:
        name = match[0].strip()
        first_percent = match[1]   # This is actually WIN RATE
        second_percent = match[2]  # This is actually PICK RATE
        
        # Skip if name is too short or contains suspicious patterns
        if len(name) < 2 or name in ['All', 'PC', 'Role']:
            continue
        
        # CORRECTED: Despite the header saying "Pick Rate Win Rate",
        # the actual data order is: Hero Name, Win Rate, Pick Rate
        heroes.append({
            'name': name,
            'pickRate': second_percent,  # ← SWAPPED
            'winRate': first_percent      # ← SWAPPED
        })
        print(f"  Added: {name}: pick={second_percent}, win={first_percent}")
    
    print(f"\nSuccessfully parsed {len(heroes)} heroes")
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
    
    print(f"Filtered to {len(filtered)} {role} heroes")
    return filtered

def scrape_all_heroes(region='Europe'):
    """Scrape all hero statistics"""
    
    url = f"https://overwatch.blizzard.com/en-us/rates/?input=PC&map=all-maps&region={region}&role=All&rq=2&tier=All"
    
    print(f"\nFetching from: {url}\n")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        print(f"HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            return parse_hero_stats(response.content)
        else:
            print(f"Failed: HTTP {response.status_code}")
            return []
            
    except Exception as e:
        print(f"Error: {e}")
        return []

def main():
    print("=" * 70)
    print("Overwatch Stats Scraper")
    print("=" * 70)
    
    all_heroes = scrape_all_heroes()
    
    if not all_heroes:
        print("\nFailed to scrape heroes")
        exit(1)
    
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
    
    total = sum(len(heroes) for heroes in data['roles'].values())
    
    with open('ow_rates.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 70)
    print(f"SUCCESS! Scraped {total} heroes")
    print(f"   Tank: {len(data['roles']['Tank'])} heroes")
    print(f"   Damage: {len(data['roles']['Damage'])} heroes")
    print(f"   Support: {len(data['roles']['Support'])} heroes")
    print("Saved to ow_rates.json")
    print("=" * 70)

if __name__ == '__main__':
    main()
