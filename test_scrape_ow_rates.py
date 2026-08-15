import unittest

from scrape_ow_rates import (
    TANK_HEROES,
    filter_heroes_by_role,
    parse_hero_stats,
)


def _rates_html(*rows: tuple[str, str, str, str]) -> str:
    """Build a minimal rates-page blob in the concatenated format the scraper parses."""
    body = "".join(f"{name}{win}{pick}{ban}" for name, win, pick, ban in rows)
    return (
        "<html><body>HeroPick RateWin RateBan Rate"
        f"{body}"
        "Frequently Asked Questions</body></html>"
    )


class ParseHeroStatsTests(unittest.TestCase):
    def test_parses_dmon_adjacent_to_dva(self):
        html = _rates_html(
            ("D.Mon", "48.9%", "14.5%", "10.8%"),
            ("D.Va", "46.2%", "6.0%", "7.9%"),
        )

        heroes = parse_hero_stats(html, verbose=False)

        self.assertEqual(
            [h["name"] for h in heroes],
            ["D.Mon", "D.Va"],
        )
        self.assertEqual(
            heroes[0],
            {
                "name": "D.Mon",
                "winRate": "48.9%",
                "pickRate": "14.5%",
                "banRate": "10.8%",
            },
        )

    def test_dmon_is_a_tank(self):
        self.assertIn("D.Mon", TANK_HEROES)

        heroes = [{"name": "D.Mon", "winRate": "48.9%", "pickRate": "14.5%", "banRate": "10.8%"}]
        tanks = filter_heroes_by_role(heroes, "Tank")
        self.assertEqual(len(tanks), 1)
        self.assertEqual(tanks[0]["name"], "D.Mon")


if __name__ == "__main__":
    unittest.main()
