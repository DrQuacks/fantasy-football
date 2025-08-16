import os, requests

LEAGUE_ID = 57220027
YEAR = 2024
WEEK = 1

url = f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/{YEAR}/segments/0/leagues/{LEAGUE_ID}"
params = {"view": "mBoxscore", "scoringPeriodId": WEEK, "matchupPeriodId": WEEK}
cookies = {"swid": os.getenv("ESPN_SWID"), "espn_s2": os.getenv("ESPN_S2")}
headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://fantasy.espn.com/"}

print("SWID present?", bool(cookies["swid"]))
print("S2 present?", bool(cookies["espn_s2"]))

r = requests.get(url, params=params, cookies=cookies, headers=headers, timeout=20)
print("Status:", r.status_code)
print(r.text[:400])