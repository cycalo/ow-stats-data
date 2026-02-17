import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time

def parse_hero_stats(html_content):
    """Parse hero statistics from HTML"""
    soup = BeautifulSoup(html_content, 'html.parser')
    heroes = []
    
    text = soup.get_text()
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Find hero data section
    try:
        start_idx = lines.index('HeroPick RateWin Rate') + 1
        
        # Find end (FAQ section)
        end_markers = ['Frequently Asked Questions', 'What patch is this data from?']
        end_idx = len(lines)
        for marker in end_markers:
            if marker in lines:
                end_idx = min(end_idx, lines.index(marker))
        
        hero_data_lines = lines[start_idx:end_idx]
    except ValueError as e:
        print(f"Could not parse hero data: {e}")
        return heroes
    
    # Parse in groups of 3 (name, pick rate, win rate)
    i = 0
    while i < len(hero_data_lines) - 2:
        hero_name = hero_data_lines[i]
        pick_rate = hero_data_lines[i + 1]
        win_rate = hero_data_lines[i + 2]
        
        # Validate percentages
        if '%' in pick_rate and '%' in win_rate:
            heroes.append({
                'name': hero_name,
                'pickRate': pick_rate,
                'winRate': win_rate
            })
            i += 3
        else:
            i += 1
    
    return heroes

def scrape_role(role, region='Europe'):
    """Scrape statistics for a specific role"""
    url = f"https://overwatch.blizzard.com/en-us/rates/?input=PC&map=all-maps&region={region}&role={role}&rq=2&tier=All"
    
    print(f"Scraping {role} heroes from {region}...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            heroes = parse_hero_stats(response.content)
            print(f"✅ Found {len(heroes)} {role} heroes")
            return heroes
        else:
            print(f"❌ Failed: HTTP {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error scraping {role}: {e}")
        return []

def main():
    print("=" * 50)
    print("Overwatch Stats Scraper")
    print("=" * 50)
    
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
    
    # Scrape each role
    roles = ['Tank', 'Damage', 'Support']
    
    for role in roles:
        data['roles'][role] = scrape_role(role)
        time.sleep(2)  # Be polite, wait between requests
    
    # Calculate totals
    total_heroes = sum(len(heroes) for heroes in data['roles'].values())
    
    # Save to JSON
    with open('ow_rates.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print("\n" + "=" * 50)
    print(f"✅ SUCCESS! Scraped {total_heroes} heroes")
    print("📄 Saved to ow_rates.json")
    print("=" * 50)

if __name__ == '__main__':
    main()
