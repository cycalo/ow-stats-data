# Overwatch Stats Data

Automatically scraped Overwatch hero statistics from Blizzard's official stats page.

## Data Source
- **Source:** https://overwatch.blizzard.com/en-us/rates/
- **Regions:** Europe, Americas, and Asia
- **Tier:** All Ranks
- **Game Mode:** Competitive - Role Queue
- **Platform:** PC (Mouse & Keyboard)

The scraper probes `rq=0`, `rq=1`, and `rq=2` and selects whichever page has non-zero hero ban rates (Quick Play always shows 0% bans). That competitive `rq` is then used for every region. The chosen URL is recorded per region.

Top-level `sourceUrl`, `region`, and `roles` stay **Europe** so existing consumers keep working. All three regions live under `regions`.

## Update Schedule
Data is automatically updated every Sunday at 2 AM UTC via GitHub Actions.

## Usage
Access the JSON file at:
```
https://cycalo.github.io/ow-stats-data/ow_rates.json
```

## Data Format
Each hero entry includes **pick**, **win**, and **ban** rates (strings with a `%` suffix), scraped from the competitive role-queue page (auto-detected `rq`).

```json
{
  "lastUpdated": "2026-02-17T02:00:00",
  "sourceUrl": "https://overwatch.blizzard.com/en-us/rates/?input=PC&map=all-maps&region=Europe&role=All&rq=2&tier=All",
  "region": "Europe",
  "regions": {
    "Europe": { "sourceUrl": "...&region=Europe...", "roles": { "Tank": [], "Damage": [], "Support": [] } },
    "Americas": { "sourceUrl": "...&region=Americas...", "roles": { "Tank": [], "Damage": [], "Support": [] } },
    "Asia": { "sourceUrl": "...&region=Asia...", "roles": { "Tank": [], "Damage": [], "Support": [] } }
  },
  "roles": {
    "Tank": [
      {"name": "Reinhardt", "pickRate": "11.3%", "winRate": "52.1%", "banRate": "2%"}
    ],
    "Damage": [...],
    "Support": [...]
  }
}
```

`roles` at the top level is the Europe snapshot (same object as `regions.Europe.roles`).

## Disclaimer
This data is sourced from Blizzard Entertainment's official statistics page. 
This project is not affiliated with or endorsed by Blizzard Entertainment.
All trademarks are property of their respective owners.
