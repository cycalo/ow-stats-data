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
# Top-level ow_rates.json fields stay Europe for existing consumers.
REGIONS = ("Europe", "Americas", "Asia")
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


def assert_rates_url(final_url: str, region: str, rq: str) -> None:
    """Abort if the response URL is not the competitive page for this region."""
    query = parse_qs(urlparse(final_url).query)
    rq_values = query.get("rq", [])
    region_values = query.get("region", [])
    if rq_values != [rq] or region_values != [region]:
        raise RuntimeError(
            f"Expected competitive {region} data (rq={rq}). "
            f"Final URL after redirects: {final_url!r} "
            f"(parsed rq={rq_values!r}, region={region_values!r})."
        )


def fetch_region(region: str, rq: str) -> tuple[list[dict], str]:
    """Fetch competitive hero stats for one region using an already chosen rq."""
    params = rates_params(region=region, rq=rq)
    print(f"Fetching {region} with rq={rq}")
    response = requests.get(
        RATES_PAGE, params=params, headers=REQUEST_HEADERS, timeout=30
    )
    print(f"  HTTP {response.status_code}: {response.url}")
    if response.status_code != 200:
        raise RuntimeError(f"{region}: HTTP {response.status_code}")

    assert_rates_url(response.url, region, rq)
    heroes = parse_hero_stats(response.content, verbose=False)
    nonzero_bans = count_nonzero_bans(heroes)
    if len(heroes) == 0 or nonzero_bans < MIN_NONZERO_BANS:
        raise RuntimeError(
            f"{region} did not look like competitive data "
            f"({len(heroes)} heroes, {nonzero_bans} with non-zero bans)."
        )
    print(f"  {region}: {len(heroes)} heroes, {nonzero_bans} with non-zero ban rates")
    return heroes, response.url


TANK_HEROES = [
    "D.Mon",
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
    "Doctrine",
    "Illari",
    "Jetpack Cat",
    "Juno",
    "Kiriko",
    "Lifeweaver",
    "Lúcio",
    "Mercy",
    "Mizuki",
    "Moira",
    "Sombra",
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

def roles_for(heroes: list[dict], region: str) -> dict[str, list[dict]]:
    """Split a region's hero list into Tank, Damage, and Support."""
    print(f"\n{region}")
    return {
        "Tank": filter_heroes_by_role(heroes, "Tank"),
        "Damage": filter_heroes_by_role(heroes, "Damage"),
        "Support": filter_heroes_by_role(heroes, "Support"),
    }


def check_role_counts(roles: dict[str, list[dict]], region: str) -> None:
    expected_counts = {"Tank": 15, "Damage": 23, "Support": 15}
    for role, expected in expected_counts.items():
        actual = len(roles[role])
        if actual != expected:
            print(f"WARNING: {region} {role} has {actual} heroes, expected {expected}")


def scrape_all_regions() -> dict[str, tuple[list[dict], str]]:
    """
    Scrape competitive stats for Europe, Americas, and Asia.

    Competitive rq is detected once (using Europe). The same rq is a game-mode
    flag, so the other regions are fetched with that value.
    """
    rq, europe_heroes, europe_url = discover_competitive_rq(region="Europe")
    scraped = {"Europe": (europe_heroes, europe_url)}

    for region in REGIONS:
        if region == "Europe":
            continue
        scraped[region] = fetch_region(region, rq)

    return scraped


def main():
    print("=" * 70)
    print("Overwatch Stats Scraper")
    print("=" * 70)

    try:
        scraped = scrape_all_regions()

        regions_payload = {}
        for region in REGIONS:
            heroes, source_url = scraped[region]
            if not heroes:
                print(f"\nERROR: Failed to scrape {region}")
                sys.exit(1)
            roles = roles_for(heroes, region)
            check_role_counts(roles, region)
            regions_payload[region] = {
                "sourceUrl": source_url,
                "roles": roles,
            }

        europe = regions_payload["Europe"]
        data = {
            "lastUpdated": datetime.now().isoformat(),
            "source": "Blizzard Entertainment Official Stats",
            # Top-level sourceUrl, region, and roles stay Europe so existing
            # consumers of ow_rates.json keep working.
            "sourceUrl": europe["sourceUrl"],
            "region": "Europe",
            "regions": regions_payload,
            "tier": "All Tiers",
            "gameMode": "Competitive - Role Queue",
            "platform": "PC (Mouse & Keyboard)",
            "disclaimer": "Not affiliated with or endorsed by Blizzard Entertainment",
            "roles": europe["roles"],
        }

        if sum(len(heroes) for heroes in data["roles"].values()) == 0:
            print("\nERROR: No heroes in final data")
            sys.exit(1)

        with open("ow_rates.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print("\n" + "=" * 70)
        print("SUCCESS! Scraped competitive stats for " + ", ".join(REGIONS))
        for region in REGIONS:
            roles = regions_payload[region]["roles"]
            total = sum(len(heroes) for heroes in roles.values())
            print(
                f"   {region}: {total} heroes "
                f"(Tank {len(roles['Tank'])}, "
                f"Damage {len(roles['Damage'])}, "
                f"Support {len(roles['Support'])})"
            )
        print("Saved to ow_rates.json")
        print("=" * 70)

    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
