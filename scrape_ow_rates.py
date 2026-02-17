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
