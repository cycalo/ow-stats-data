# Overwatch Stats Data

Automatically scraped Overwatch hero statistics from Blizzard's official stats page.

## Data Source
- **Source:** https://overwatch.blizzard.com/en-us/rates/
- **Region:** Europe
- **Tier:** All Ranks
- **Game Mode:** Competitive - Role Queue
- **Platform:** PC (Mouse & Keyboard)

## Update Schedule
Data is automatically updated every Sunday at 2 AM UTC via GitHub Actions.

## Usage
Access the JSON file at:
```
https://yourusername.github.io/ow-stats-data/ow_rates.json
```

## Data Format
```json
{
  "lastUpdated": "2026-02-17T02:00:00",
  "roles": {
    "Tank": [
      {"name": "Reinhardt", "pickRate": "52.3%", "winRate": "12.3%"}
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
```

---

### **Step 3: Enable GitHub Pages**

1. Go to your repo on GitHub
2. Click **Settings** (top menu)
3. Scroll down to **Pages** (left sidebar)
4. Under "Source":
   - Branch: `main`
   - Folder: `/ (root)`
5. Click **Save**
6. Wait 2-3 minutes
7. Your JSON will be available at:
```
   https://yourusername.github.io/ow-stats-data/ow_rates.json
