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
        first_percent = match[1]   # This is PICK RATE
        second_percent = match[2]  # This is WIN RATE
        
        # Skip if name is too short or contains suspicious patterns
        if len(name) < 2 or name in ['All', 'PC', 'Role']:
            continue
        
        heroes.append({
            'name': name,
            'pickRate': first_percent,   # ← SWAPPED
            'winRate': second_percent     # ← SWAPPED
        })
        print(f"  ✓ {name}: {first_percent} pick, {second_percent} win")
    
    print(f"\nSuccessfully parsed {len(heroes)} heroes")
    return heroes
```

**Actually wait...** Let me verify the order first.

---

## **Let me check the actual order:**

Can you tell me what you see on this page for **Ana** and **Reinhardt**?

https://overwatch.blizzard.com/en-us/rates/?input=PC&map=all-maps&region=Europe&role=All&rq=2&tier=All

**For Ana:**
- Pick Rate: ?
- Win Rate: ?

**For Reinhardt:**
- Pick Rate: ?
- Win Rate: ?

This will help me confirm which percentage comes first in the actual HTML.

---

## **Meanwhile, here's a test:**

The current scraper captures them as:
```
match[1] = first percentage
match[2] = second percentage
