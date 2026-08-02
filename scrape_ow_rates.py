import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from urllib.parse import parse_qs, urlparse
import re
import sys

# Blizzard rotates which rq value (0/1/2) maps to Competitive; we detect it at runtime.
RATES_PAGE = "https://overwatch.blizzard.com/en-us/rates/"
RQ_CANDIDATES = ("0", "1", "2")
MIN_NONZERO_BANS = 10
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def rates_params(region: str, rq: str) -> dict[str, str]:
    """Query string for official PC stats at a given rq value."""
    return {
        "input": "PC",
        "map": "all-maps",
        "region": region,
        "role": "All",
        "rq": rq,
        "tier": "All",
    }


def count_nonzero_bans(heroes: list[dict]) -> int:
    """Quick Play always has 0% bans; competitive has many non-zero ban rates."""
    return sum(1 for hero in heroes if hero["banRate"] != "0%")


def rq_from_source_url(source_url: str) -> str | None:
    """Extract the rq query param from a Blizzard rates URL, if present."""
    rq_values = parse_qs(urlparse(source_url).query).get("rq", [])
    return rq_values[0] if len(rq_values) == 1 else None


def load_previous_rq(path: str = "ow_rates.json") -> str | None:
    """Return the rq value recorded in the last scrape output, if available."""
    try:
        with open(path, encoding="utf-8") as f:
            return rq_from_source_url(json.load(f).get("sourceUrl", ""))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def discover_competitive_rq(region: str = "Europe") -> tuple[str, list[dict], str]:
    """
    Probe rq=0/1/2 and return whichever serves competitive role-queue data.

    Competitive pages have many heroes with non-zero ban rates; Quick Play does not.
    """
    results: list[tuple[int, str, list[dict], str]] = []

    print("Discovering competitive rq value (probing 0, 1, 2)...")
    for rq in RQ_CANDIDATES:
        params = rates_params(region=region, rq=rq)
        response = requests.get(
            RATES_PAGE, params=params, headers=REQUEST_HEADERS, timeout=30
        )
        if response.status_code != 200:
            print(f"  rq={rq}: HTTP {response.status_code}, skipping")
            continue

        heroes = parse_hero_stats(response.content, verbose=False)
        nonzero_bans = count_nonzero_bans(heroes)
        print(
            f"  rq={rq}: {len(heroes)} heroes, "
            f"{nonzero_bans} with non-zero ban rates"
        )
        results.append((nonzero_bans, rq, heroes, response.url))

    if not results:
        raise RuntimeError("Failed to fetch hero data for any rq candidate.")

    results.sort(key=lambda item: item[0], reverse=True)
    best_bans, best_rq, best_heroes, best_url = results[0]

    if best_bans < MIN_NONZERO_BANS:
        summary = ", ".join(f"rq={rq}:{bans}" for bans, rq, _, _ in results)
        raise RuntimeError(
            "Could not identify competitive data: no rq value had enough non-zero "
            f"ban rates (need >= {MIN_NONZERO_BANS}). Probed: {summary}"
        )

    if len(results) > 1 and results[1][0] == best_bans:
        tied = [rq for bans, rq, _, _ in results if bans == best_bans]
        raise RuntimeError(
            "Ambiguous competitive rq detection: multiple rq values had the same "
            f"non-zero ban count ({best_bans}): {', '.join(tied)}"
        )

    previous_rq = load_previous_rq()
    if previous_rq and previous_rq != best_rq:
        print(
            f"NOTE: Competitive rq changed since last scrape "
            f"({previous_rq} -> {best_rq})"
        )

    print(f"Using competitive rq={best_rq} ({best_bans} heroes with ban data)")
    return best_rq, best_heroes, best_url


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


def parse_hero_stats(html_content, verbose: bool = True):
    """
    Parse hero stats from page text.

    The official table order in the scraped blob is: Win %, Pick %, Ban % (after each
    hero name). A leading ``Ban Rate`` label is stripped when present.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    heroes = []

    text = soup.get_text()
    if verbose:
        print(f"Content length: {len(text)} characters")

    hero_section_match = re.search(
        r"HeroPick RateWin Rate(.+?)Frequently Asked Questions",
        text,
        re.DOTALL,
    )

    if not hero_section_match:
        if verbose:
            print("ERROR: Could not find hero data section")
            print("Dumping first 1000 chars of text:")
            print(text[:1000])
        return heroes

    hero_data = hero_section_match.group(1)
    if verbose:
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
            if verbose:
                tail = hero_data[i : i + 80].replace("\n", " ")
                print(f"ERROR: Could not match a known hero name at offset {i}: {tail!r}")
            return []

        i += len(matched_name)
        m = _TRIPLE_PCT.match(hero_data[i:])
        if not m:
            if verbose:
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

    if verbose:
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
    """Scrape competitive role-queue stats, auto-detecting the active rq value."""
    try:
        _, all_heroes, source_url = discover_competitive_rq(region=region)
        print(f"Final URL: {source_url}")
        print(f"Successfully parsed {len(all_heroes)} heroes")

        print("\nHeroes found:")
        for hero in sorted(all_heroes, key=lambda h: h["name"]):
            print(
                f"  - {hero['name']}: pick={hero['pickRate']}, "
                f"win={hero['winRate']}, ban={hero['banRate']}"
            )

        return all_heroes, source_url

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
