import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from urllib.parse import parse_qs, urlparse
import re
import sys

# Blizzard "rq" query param: 0 = Quick Play, 1 = Competitive, 2 = Quick Play (legacy alias).
RATES_PAGE = "https://overwatch.blizzard.com/en-us/rates/"
COMPETITIVE_RQ = "1"


def competitive_rates_params(region: str = "Europe") -> dict[str, str]:
    """Query string for official PC competitive stats (rq=1)."""
    return {
        "input": "PC",
        "map": "all-maps",
        "region": region,
        "role": "All",
        "rq": COMPETITIVE_RQ,
        "tier": "All",
    }


def assert_final_url_is_competitive(final_url: str) -> None:
    """Abort if redirects or server rewrote the queue mode away from competitive."""
    parsed = urlparse(final_url)
    rq_values = parse_qs(parsed.query).get("rq", [])
    if len(rq_values) != 1 or rq_values[0] != COMPETITIVE_RQ:
        raise RuntimeError(
            "Expected competitive data (rq=1 only). "
            f"Final URL after redirects: {final_url!r} "
            f"(parsed rq={rq_values!r}). Refusing to scrape Quick Play or unknown modes."
        )


TANK_HEROES = [
    "D.Va",
    "Doomfist",
    "Domina",
    "Hazard",
    "Junker Queen",
    "Mauga",
    "Orisa",
    "Ramattra",
    "Reinhardt",
    "Roadhog",
    "Sigma",
    "Winston",
    "Wrecking Ball",
    "Zarya",
]

DAMAGE_HEROES = [
    "Anran",
    "Ashe",
    "Bastion",
    "Cassidy",
    "Echo",
    "Emre",
    "Freja",
    "Genji",
    "Hanzo",
    "Junkrat",
    "Mei",
    "Pharah",
    "Reaper",
    "Shion",
    "Sierra",
    "Sojourn",
    "Soldier: 76",
    "Sombra",
    "Symmetra",
    "Torbjörn",
    "Tracer",
    "Vendetta",
    "Venture",
    "Widowmaker",
]

SUPPORT_HEROES = [
    "Ana",
    "Baptiste",
    "Brigitte",
    "Illari",
    "Jetpack Cat",
    "Juno",
    "Kiriko",
    "Lifeweaver",
    "Lúcio",
    "Mercy",
    "Mizuki",
    "Moira",
    "Wuyang",
    "Zenyatta",
]

# Blizzard concatenates hero rows with no delimiter; match longest names first.
HERO_NAMES_LONGEST_FIRST = sorted(
    set(TANK_HEROES) | set(DAMAGE_HEROES) | set(SUPPORT_HEROES),
    key=len,
    reverse=True,
)

_TRIPLE_PCT = re.compile(r"^(\d+(?:\.\d+)?%)(\d+(?:\.\d+)?%)(\d+(?:\.\d+)?%)")


def parse_hero_stats(html_content):
    """
    Parse hero stats from page text.

    The official table order in the scraped blob is: Win %, Pick %, Ban % (after each
    hero name). A leading ``Ban Rate`` label is stripped when present.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    heroes = []

    text = soup.get_text()
    print(f"Content length: {len(text)} characters")

    hero_section_match = re.search(
        r"HeroPick RateWin Rate(.+?)Frequently Asked Questions",
        text,
        re.DOTALL,
    )

    if not hero_section_match:
        print("ERROR: Could not find hero data section")
        print("Dumping first 1000 chars of text:")
        print(text[:1000])
        return heroes

    hero_data = hero_section_match.group(1)
    print(f"Found hero data section: {len(hero_data)} characters")

    if hero_data.startswith("Ban Rate"):
        hero_data = hero_data[len("Ban Rate") :]

    i = 0
    while i < len(hero_data):
        if hero_data[i].isspace():
            i += 1
            continue

        matched_name = None
        for name in HERO_NAMES_LONGEST_FIRST:
            if hero_data.startswith(name, i):
                matched_name = name
                break

        if matched_name is None:
            tail = hero_data[i : i + 80].replace("\n", " ")
            print(f"ERROR: Could not match a known hero name at offset {i}: {tail!r}")
            return []

        i += len(matched_name)
        m = _TRIPLE_PCT.match(hero_data[i:])
        if not m:
            tail = hero_data[i : i + 40].replace("\n", " ")
            print(
                f"ERROR: Expected three percentages after {matched_name!r}, "
                f"got: {tail!r}"
            )
            return []

        win_rate, pick_rate, ban_rate = m.groups()
        i += m.end()

        heroes.append(
            {
                "name": matched_name,
                "winRate": win_rate,
                "pickRate": pick_rate,
                "banRate": ban_rate,
            }
        )

    print(f"Successfully parsed {len(heroes)} heroes")

    print("\nHeroes found:")
    for hero in sorted(heroes, key=lambda h: h["name"]):
        print(
            f"  - {hero['name']}: pick={hero['pickRate']}, "
            f"win={hero['winRate']}, ban={hero['banRate']}"
        )

    return heroes

def filter_heroes_by_role(heroes, role):
    """Filter heroes by their actual role"""

    if role == "Tank":
        filtered = [h for h in heroes if h["name"] in TANK_HEROES]
    elif role == "Damage":
        filtered = [h for h in heroes if h["name"] in DAMAGE_HEROES]
    elif role == "Support":
        filtered = [h for h in heroes if h["name"] in SUPPORT_HEROES]
    else:
        return heroes

    print(f"Filtered to {len(filtered)} {role} heroes")

    if role == "Tank":
        expected = TANK_HEROES
    elif role == "Damage":
        expected = DAMAGE_HEROES
    else:
        expected = SUPPORT_HEROES

    found_names = [h["name"] for h in filtered]
    missing = [name for name in expected if name not in found_names]
    if missing:
        print(f"WARNING: Missing {len(missing)} {role} heroes: {', '.join(missing)}")

    return filtered

def scrape_all_heroes(region: str = "Europe"):
    """Scrape all hero statistics from Competitive (rq=1), not Quick Play (rq=0)."""
    params = competitive_rates_params(region=region)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    print(f"Fetching from: {RATES_PAGE} with params {params}")

    try:
        response = requests.get(
            RATES_PAGE, params=params, headers=headers, timeout=30
        )

        print(f"HTTP Status: {response.status_code}")
        print(f"Final URL: {response.url}")

        if response.status_code != 200:
            print(f"ERROR: HTTP {response.status_code}")
            return [], ""

        assert_final_url_is_competitive(response.url)

        return parse_hero_stats(response.content), response.url

    except Exception as e:
        print(f"ERROR fetching data: {e}")
        import traceback

        traceback.print_exc()
        return [], ""

def main():
    print("=" * 70)
    print("Overwatch Stats Scraper")
    print("=" * 70)
    
    try:
        all_heroes, source_url = scrape_all_heroes()

        if not all_heroes:
            print("\nERROR: Failed to scrape heroes")
            sys.exit(1)

        data = {
            'lastUpdated': datetime.now().isoformat(),
            'source': 'Blizzard Entertainment Official Stats',
            'sourceUrl': source_url,
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
        expected_counts = {'Tank': 14, 'Damage': 24, 'Support': 14}
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
