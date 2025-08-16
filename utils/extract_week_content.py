# extract_week_context.py
import os
import json
from pathlib import Path
import shutil
from typing import Dict, Any, List

import pandas as pd
from espn_v3_client import ESPNV3Client

LEAGUE_ID = 57220027
YEAR = 2024
WEEKS = range(1, 19)  # adjust if needed

OUT_PARQUET = f"data/espn_week_context_{YEAR}.parquet"
OUT_CSV = f"data/espn_week_context_{YEAR}.csv"

def parse_boxscores_to_rows(raw: Dict[str, Any], year: int, week: int) -> List[Dict[str, Any]]:
    """
    Normalize mBoxscore JSON into per-player/week rows.
    Works with the common structure returned by ESPN v3.
    """
    rows = []

    # Most seasons expose 'schedule' array with 'home'/'away' teams and 'boxscore' blocks.
    schedule = raw.get("schedule", [])
    for match in schedule:
        box = match.get("boxscore") or match  # some seasons nest under 'boxscore', others inline

        # home & away lineups often sit under these keys; sometimes 'home'/'away' contain 'rosterForCurrentScoringPeriod'
        home_players = []
        away_players = []

        # Try typical structure first
        if "home" in box and isinstance(box["home"], dict):
            home_players = box["home"].get("rosterForCurrentScoringPeriod", {}).get("entries", [])
        if "away" in box and isinstance(box["away"], dict):
            away_players = box["away"].get("rosterForCurrentScoringPeriod", {}).get("entries", [])

        # Fallbacks: some seasons use 'homeRoster'/'awayRoster' or 'homeLineup'/'awayLineup'
        if not home_players:
            home_players = box.get("homeRoster", []) or box.get("homeLineup", [])
        if not away_players:
            away_players = box.get("awayRoster", []) or box.get("awayLineup", [])

        def extract_player(entry: Dict[str, Any]) -> Dict[str, Any]:
            """
            Extract a single player's weekly context from a roster/entry object.
            Different seasons expose slightly different shapes; we handle common ones.
            """
            # Entry can be { 'playerPoolEntry': { 'player': {...} }, 'lineupSlotId': ..., 'playerId': ... }
            p_obj = entry.get("playerPoolEntry", {}).get("player", {}) or entry.get("player", {})
            stats_block = entry.get("playerPoolEntry", {}).get("appliedStatTotal")  # sometimes points here
            # Fallbacks for points/projections are later.

            player_id = p_obj.get("id") or entry.get("playerId")
            name = p_obj.get("fullName") or p_obj.get("name")
            pro_team_abbr = p_obj.get("proTeamAbbreviation") or p_obj.get("proTeam")
            # Opponent often lives on the line item under 'opponentProTeamAbbreviation' or similar key:
            pro_opp = entry.get("opponentProTeamAbbreviation") or entry.get("proOpponent") or entry.get("opponent")

            # Slot (fantasy lineup position)
            slot = entry.get("lineupSlotId") or entry.get("slotCategoryId") or entry.get("lineupSlot")
            # If you want human-readable slot names, map IDs later.

            # Game date / played flags may sit under 'p_obj' or 'entry'
            game_date = entry.get("gameDate") or p_obj.get("gameDate")
            game_played = entry.get("gamePlayed") or p_obj.get("gamePlayed")  # 0 or 100
            on_bye = entry.get("onBye") or p_obj.get("onBye") or False
            active_status = entry.get("activeStatus") or p_obj.get("activeStatus")

            # Points / projected points can be in different places
            points = entry.get("appliedStatTotal") or entry.get("points") or stats_block or 0.0
            projected_points = entry.get("appliedProjectedStatTotal") or entry.get("projectedPoints") or 0.0

            return {
                "year": year,
                "week": week,
                "playerId": int(player_id) if player_id is not None else None,
                "name": name,
                "pro_team": pro_team_abbr,
                "pro_opponent": pro_opp,
                "slot_position": slot,
                "game_date": game_date,
                "played": (game_played == 100) if isinstance(game_played, int) else None,
                "on_bye_week": bool(on_bye),
                "active_status": active_status,
                "points": float(points) if points is not None else 0.0,
                "projected_points": float(projected_points) if projected_points is not None else 0.0,
            }

        for entry in home_players:
            rows.append(extract_player(entry))
        for entry in away_players:
            rows.append(extract_player(entry))

    return rows

def main():
    if os.path.isdir(".cache/espn_v3"):
        shutil.rmtree(".cache/espn_v3")
    client = ESPNV3Client(
        league_id=LEAGUE_ID,
        year=YEAR,
        swid=os.getenv("ESPN_SWID"),
        espn_s2=os.getenv("ESPN_S2"),
        use_cache=True,
    )
    print("Cookies present? SWID:", bool(os.getenv("ESPN_SWID")), " S2:", bool(os.getenv("ESPN_S2")))

    raw = client.get_boxscores(week=1)   # try week 1
    print("Top-level type:", type(raw), " keys:", list(raw.keys())[:10] if isinstance(raw, dict) else None)

    all_rows: List[Dict[str, Any]] = []
    for w in WEEKS:
        raw = client.get_boxscores(w)
        rows = parse_boxscores_to_rows(raw, YEAR, w)
        print(f"Week {w}: extracted {len(rows)} rows")
        all_rows.extend(rows)

    df = pd.DataFrame(all_rows)
    # Basic cleanups
    df = df.dropna(subset=["playerId"]).reset_index(drop=True)

    # Optional: coerce types
    df["week"] = df["week"].astype(int)
    df["year"] = df["year"].astype(int)
    df["playerId"] = df["playerId"].astype(int)

    Path(OUT_PARQUET).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT_PARQUET, index=False)
    df.to_csv(OUT_CSV, index=False)
    print(f"✅ Wrote {len(df)} rows to:\n  - {OUT_PARQUET}\n  - {OUT_CSV}")

    # Quick peek
    print(df.head(10))

if __name__ == "__main__":
    main()
