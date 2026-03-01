import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re
import sys

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
        print("Dumping first 1000 chars of text:")
        print(text[:1000])
        return heroes
    
    hero_data = hero_section_match.group(1)
    print(f"Found hero data section: {len(hero_data)} characters")
    
    # SPECIAL CASE: Handle "Soldier: 76" first
    # Pattern specifically for Soldier: 76
    soldier_pattern = r'(Soldier: 76)(\d+(?:\.\d+)?%)(\d+(?:\.\d+)?%)'
    soldier_match = re.search(soldier_pattern, hero_data)
    
    if soldier_match:
        print("Found Soldier: 76!")
        heroes.append({
            'name': 'Soldier: 76',
            'pickRate': soldier_match.group(3),  # SWAPPED (pick is second %)
            'winRate': soldier_match.group(2)     # SWAPPED (win is first %)
        })
        # Remove Soldier: 76 from the data so it doesn't get matched again
        hero_data = hero_data.replace(soldier_match.group(0), '', 1)
    else:
        print("WARNING: Soldier: 76 not found!")
    
    # GENERAL PATTERN: Match all other heroes
    # Matches: Any characters (except digits) followed by two percentages
    pattern = r'([^0-9]+?)(\d+(?:\.\d+)?%)(\d+(?:\.\d+)?%)'
    
    matches = re.findall(pattern, hero_data)
    
    print(f"Found {len(matches)} additional hero entries")
    
    if len(matches) == 0 and len(heroes) == 0:
        print("ERROR: No matches found at all")
        print("Hero data content:")
        print(hero_data[:500])
        return heroes
    
    # Filter out junk matches
    for match in matches:
        name = match[0].strip()
        first_percent = match[1]   # This is WIN RATE
        second_percent = match[2]  # This is PICK RATE
        
        # Skip if name is too short
        if len(name) < 2:
            continue
            
        # Skip common false positives
        skip_terms = [
            'All', 'PC', 'Role', 'Map', 'Region', 'Input', 'Game Mode',
            'Tier', 'Quick Play', 'Competitive', 'Bronze', 'Silver', 'Gold',
            'Platinum', 'Diamond', 'Master', 'Grandmaster', 'Champion',
            'Mouse', 'Keyboard', 'Controller', 'Americas', 'Asia', 'Europe',
            'Pick Rate', 'Win Rate', 'Hero', 'Soldier'
        ]
        
        if any(term in name for term in skip_terms):
            continue
        
        # Skip if name contains numbers (we already handled Soldier: 76)
        if any(char.isdigit() for char in name):
            continue
        
        # Data order from Blizzard: Hero Name, Win Rate, Pick Rate
        # But we want: Hero Name, Pick Rate, Win Rate
        heroes.append({
            'name': name,
            'pickRate': second_percent,  # SWAPPED
            'winRate': first_percent     # SWAPPED
        })
    
    print(f"Successfully parsed {len(heroes)} heroes total (including Soldier: 76)")
    
    # Debug: print all hero names found
    print("\nHeroes found:")
    for hero in sorted(heroes, key=lambda h: h['name']):
        print(f"  - {hero['name']}: pick={hero['pickRate']}, win={hero['winRate']}")
    
    return heroes

def filter_heroes_by_role(heroes, role):
    """Filter heroes by their actual role"""
    
    TANK_HEROES = [
        'D.Va', 'Doomfist', 'Domina', 'Hazard', 'Junker Queen', 'Mauga', 
        'Orisa', 'Ramattra', 'Reinhardt', 'Roadhog', 'Sigma', 
        'Winston', 'Wrecking Ball', 'Zarya'
    ]
    
    DAMAGE_HEROES = [
        'Anran', 'Ashe', 'Bastion', 'Cassidy', 'Echo', 'Emre', 'Freja', 'Genji', 
        'Hanzo', 'Junkrat', 'Mei', 'Pharah', 'Reaper', 'Sojourn', 
        'Soldier: 76', 'Sombra', 'Symmetra', 'Torbjörn', 'Tracer', 
        'Vendetta', 'Venture', 'Widowmaker'
    ]
    
    SUPPORT_HEROES = [
        'Ana', 'Baptiste', 'Brigitte', 'Illari', 'Jetpack Cat', 
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
    
    # Check for missing heroes
    if role == 'Tank':
        expected = TANK_HEROES
    elif role == 'Damage':
        expected = DAMAGE_HEROES
    else:
        expected = SUPPORT_HEROES
    
    found_names = [h['name'] for h in filtered]
    missing = [name for name in expected if name not in found_names]
    if missing:
        print(f"WARNING: Missing {len(missing)} {role} heroes: {', '.join(missing)}")
    
    return filtered

def scrape_all_heroes(region='Europe'):
    """Scrape all hero statistics"""
    
    url = f"https://overwatch.blizzard.com/en-us/rates/?input=PC&map=all-maps&region=Europe&role=All&rq=1&tier=All"
    
    print(f"Fetching from: {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        print(f"HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            return parse_hero_stats(response.content)
        else:
            print(f"ERROR: HTTP {response.status_code}")
            return []
            
    except Exception as e:
        print(f"ERROR fetching data: {e}")
        import traceback
        traceback.print_exc()
        return []

def main():
    print("=" * 70)
    print("Overwatch Stats Scraper")
    print("=" * 70)
    
    try:
        all_heroes = scrape_all_heroes()
        
        if not all_heroes:
            print("\nERROR: Failed to scrape heroes")
            sys.exit(1)
        
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
        
        if total == 0:
            print("\nERROR: No heroes in final data")
            sys.exit(1)
        
        # Verify expected hero counts
        expected_counts = {'Tank': 14, 'Damage': 22, 'Support': 14}
        for role, expected in expected_counts.items():
            actual = len(data['roles'][role])
            if actual != expected:
                print(f"\nWARNING: {role} has {actual} heroes, expected {expected}")
        
        with open('ow_rates.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print("\n" + "=" * 70)
        print(f"SUCCESS! Scraped {total} heroes")
        print(f"   Tank: {len(data['roles']['Tank'])} heroes")
        print(f"   Damage: {len(data['roles']['Damage'])} heroes")
        print(f"   Support: {len(data['roles']['Support'])} heroes")
        print("Saved to ow_rates.json")
        print("=" * 70)
        
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
