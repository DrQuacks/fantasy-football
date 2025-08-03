from espn_api.football import League

import time

LEAGUE_ID = 57220027  # replace with your actual league ID
START_YEAR = 2019
END_YEAR = 2024

espn_s2 = 'your_espn_s2_cookie'  # needed if league is private
swid = '{your_swid_cookie}'

for year in range(START_YEAR, END_YEAR + 1):
    try:
        league = League(league_id=LEAGUE_ID, year=year)
        teams = [team.team_name for team in league.teams]
        print(f"{year}: SUCCESS – Teams: {teams}")
    except Exception as e:
        print(f"{year}: Not available ({e})")
    time.sleep(1)  # be polite to ESPN servers

league = League(league_id=57220027, year=2024)

# Print basic league info
print(f"Teams in league: {[team.team_name for team in league.teams]}")
print(f"Current week: {league.current_week}")