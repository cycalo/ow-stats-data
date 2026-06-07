# Overwatch Stats Data

Automatically scraped Overwatch hero statistics from Blizzard's official stats page.

## Data Source
- **Source:** https://overwatch.blizzard.com/en-us/rates/?input=PC&map=all-maps&region=Europe&role=All&rq=1&tier=All
- **Region:** Europe
- **Tier:** All Ranks
- **Game Mode:** Competitive - Role Queue
- **Platform:** PC (Mouse & Keyboard)

## Update Schedule
Data is automatically updated every Sunday at 2 AM UTC via GitHub Actions.

## Usage
Access the JSON file at:
```
https://cycalo.github.io/ow-stats-data/ow_rates.json
```

## Data Format
Each hero entry includes **pick**, **win**, and **ban** rates (strings with a `%` suffix), scraped from the competitive page (`rq=1`).

```json
{
  "lastUpdated": "2026-02-17T02:00:00",
  "sourceUrl": "https://overwatch.blizzard.com/en-us/rates/?input=PC&map=all-maps&region=Europe&role=All&rq=1&tier=All",
  "roles": {
    "Tank": [
      {"name": "Reinhardt", "pickRate": "11.3%", "winRate": "52.1%", "banRate": "2%"}
    ],
    "Damage": [...],
    "Support": [...]
  }
}
```

## Disclaimer
This data is sourced from Blizzard Entertainment's official statistics page. 
This project is not affiliated with or endorsed by Blizzard Entertainment.
All trademarks are property of their respective owners.
