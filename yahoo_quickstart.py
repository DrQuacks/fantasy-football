import os
import sys
from yahoo_oauth import OAuth2
from yahoo_fantasy_api import game
from dotenv import load_dotenv

"""
Usage:
  1) pip install yahoo-fantasy-api yahoo-oauth python-dotenv pandas
  2) Copy .env.example to .env and fill in:
       YAHOO_CLIENT_ID, YAHOO_CLIENT_SECRET, YAHOO_REDIRECT_URI
  3) python yahoo_quickstart.py [SPORT] [YEAR]
     Example: python yahoo_quickstart.py nfl 2025
"""

def main():
    load_dotenv()
    CLIENT_ID = os.getenv('YAHOO_CLIENT_ID')
    CLIENT_SECRET = os.getenv('YAHOO_CLIENT_SECRET')
    REDIRECT_URI = os.getenv('YAHOO_REDIRECT_URI', 'http://127.0.0.1:8000/callback')

    if not CLIENT_ID or not CLIENT_SECRET:
        print("Missing CLIENT_ID or CLIENT_SECRET in env.")
        sys.exit(1)

    SPORT = sys.argv[1] if len(sys.argv) > 1 else 'nfl'
    YEAR = int(sys.argv[2]) if len(sys.argv) > 2 else 2025

    sc = OAuth2(CLIENT_ID, CLIENT_SECRET, redirect_uri=REDIRECT_URI)
    if not sc.token_is_valid():
        sc.refresh_access_token()

    # Yahoo API: get a game object for your sport/year
    g = game.Game(sc, SPORT)
    leagues = g.league_ids(YEAR)
    if not leagues:
        print(f"No {SPORT.upper()} leagues found for {YEAR}")
        return

    league_id = leagues[0]
    print(f"Using league ID: {league_id}")

    lg = g.to_league(league_id)

    # League settings
    settings = lg.settings()
    print("\n== League Settings ==")
    print("Name:", settings.get('name'))
    print("Roster Positions:", settings.get('roster_positions'))

    # Standings
    standings = lg.standings()
    print("\n== Standings (Top 5) ==")
    for row in standings[:5]:
        print(row.get('name'), row.get('outcome_totals'))

    # First team roster
    teams = lg.teams()
    if teams:
        team_key = teams[0]['team_key']
        roster = lg.to_team(team_key).roster()
        print(f"\n== Sample Roster for {teams[0]['name']} ==")
        for p in roster[:10]:
            print(p.get('display_position'), p.get('name'))

if __name__ == "__main__":
    main()
