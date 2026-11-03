"""
MLB promotion scraper 

"""

from selenium import webdriver
import csv
import re
import time

MATCHUP_RE = re.compile(
    r'^(?P<t1>[A-Z]+)\s*(?P<sep>vs|@)\s*(?P<t2>[A-Z]+) on (?P<month>\d{1,2})/(?P<day>\d{1,2})$'
)


def scrape_promo_data(url, driver):
    driver.get(url)
    time.sleep(5)  # let the JS-rendered schedule populate

    elements = driver.find_elements("css selector", "[data-tracking-matchup-with-date]")

    seen = set()
    results = []
    for el in elements:
        matchup = el.get_attribute("data-tracking-matchup-with-date")
        promo = el.get_attribute("data-tracking-featured-promotion")
        if not matchup:
            continue  # skip the empty placeholder/legend element
        key = (matchup, promo)
        if key in seen:
            continue  # page renders duplicate markup for mobile/desktop layouts
        seen.add(key)
        results.append((matchup, promo))

    return results


def parse_home_game(matchup, promo, year):
    """
    Parse a raw matchup string + promo string into a row dict, but ONLY for
    home games ('vs'). Away games ('@') return None and get filtered out.
    """
    m = MATCHUP_RE.match(matchup.strip())
    if not m:
        print(f"  Could not parse matchup string: {matchup!r}")
        return None

    if m.group("sep") != "vs":
        return None  # away game -- no real promotion data here, skip

    team = m.group("t1")
    opponent = m.group("t2")
    month, day = int(m.group("month")), int(m.group("day"))

    return {
        "team": team,
        "year": year,
        "date": f"{year}-{month:02d}-{day:02d}",
        "opponent": opponent,
        "promotion": "" if promo == "[no promotion]" else promo,
    }


def save_rows(rows, filename, write_header):
    fieldnames = ["team", "year", "date", "opponent", "promotion"]
    with open(filename, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerows(rows)


def main():
    years = [2025]
    teams = ["dbacks", "braves", "orioles", "redsox", "whitesox", "cubs", "reds",
              "guardians", "rockies", "tigers", "astros", "royals", "angels",
              "dodgers", "marlins", "brewers", "twins", "mets", "athletics",
              "phillies", "pirates", "padres", "mariners", "giants", "cardinals",
              "rays", "rangers", "yankees", "bluejays", "nationals"]

    out_file = "/Users/liu/Downloads/mlb_promotions.csv"
    write_header = True

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)

    try:
        progress_count = 0
        total = len(years) * len(teams)
        for year in years:
            for team_slug in teams:
                url = f"https://www.mlb.com/{team_slug}/schedule/{year}/fullseason"
                try:
                    raw = scrape_promo_data(url, driver)
                    rows = []
                    for matchup, promo in raw:
                        row = parse_home_game(matchup, promo, year)
                        if row:
                            rows.append(row)
                    save_rows(rows, out_file, write_header)
                    write_header = False
                    print(f"  {team_slug} {year}: {len(rows)} home games collected")
                except Exception as e:
                    print(f"Failed on {team_slug} {year}: {e}")

                progress_count += 1
                print(f"Progress: {progress_count}/{total}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()