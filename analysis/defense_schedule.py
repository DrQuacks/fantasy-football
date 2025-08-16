from espn_api.football import League
import argparse
import os
import json
from datetime import datetime
from typing import Dict, List


def collect_defense_schedule(year: int, league_id: int = 57220027) -> Dict[str, List[dict]]:
    """
    Build D/ST schedules using the player_info() map (not limited to fantasy rosters),
    reading each defense's `schedule` and `stats` fields.
    Grouped by real NFL team abbrev (player.proTeam).
    """
    league = League(
        league_id=league_id,
        year=year,
        espn_s2=os.getenv("ESPN_S2"),
        swid=os.getenv("ESPN_SWID"),
    )

    all_players = league.player_info()  # dict of playerId -> Player (may be None on some setups)
    schedule_by_team: Dict[str, List[dict]] = {}

    if all_players:
        for player in all_players.values():
            name = getattr(player, "name", "") or ""
            position = getattr(player, "position", None)
            eligible = set(getattr(player, "eligibleSlots", []) or [])
            is_dst = (
                position == "D/ST"
                or name.endswith(" D/ST")
                or "D/ST" in eligible
            )
            if not is_dst:
                continue

            pro_team = getattr(player, "proTeam", None)
            player_stats = getattr(player, "stats", {}) or {}
            schedule = getattr(player, "schedule", {}) or {}
            if not pro_team:
                # Skip if we can't attribute to a team
                continue

            team_rows: List[dict] = []
            # Use schedule weeks 1..18 to gather opponent/date; enrich with points if available
            for wk in range(1, 19):
                wk_key = str(wk)
                sch = schedule.get(wk_key) or schedule.get(wk)
                if not sch:
                    continue
                opponent = sch.get("team")
                date_str = str(sch.get("date")) if sch.get("date") is not None else None
                stat = player_stats.get(wk_key) or player_stats.get(wk) or {}
                points = stat.get("points")
                projected = stat.get("projected_points")
                team_rows.append({
                    "week": wk,
                    "opponent": opponent,
                    "date": date_str,
                    "points": points,
                    "projected_points": projected,
                    "bye": False,
                })

            if team_rows:
                team_rows.sort(key=lambda r: r["week"])
                if pro_team not in schedule_by_team:
                    schedule_by_team[pro_team] = team_rows
                else:
                    have_weeks = {r["week"] for r in schedule_by_team[pro_team]}
                    for r in team_rows:
                        if r["week"] not in have_weeks:
                            schedule_by_team[pro_team].append(r)
                    schedule_by_team[pro_team].sort(key=lambda r: r["week"])

    # Fallback: derive by picking any offensive player per NFL team and using their schedule
    if not schedule_by_team:
        seen_team: Dict[str, bool] = {}
        # scan all rosters across fantasy teams to find at least one player for each NFL team
        for team in league.teams:
            for p in team.roster:
                pro_team = getattr(p, "proTeam", None)
                if not pro_team or seen_team.get(pro_team):
                    continue
                stats = getattr(p, "stats", {}) or {}
                schedule = getattr(p, "schedule", {}) or {}
                rows: List[dict] = []
                for wk in range(1, 19):
                    wk_key = str(wk)
                    sch = schedule.get(wk_key) or schedule.get(wk)
                    if not sch:
                        continue
                    opponent = sch.get("team")
                    date_str = str(sch.get("date")) if sch.get("date") is not None else None
                    stat = stats.get(wk_key) or stats.get(wk) or {}
                    points = stat.get("points")
                    projected = stat.get("projected_points")
                    rows.append({
                        "week": wk,
                        "opponent": opponent,
                        "date": date_str,
                        "points": points,
                        "projected_points": projected,
                        "bye": False,
                    })
                if rows:
                    schedule_by_team[pro_team] = sorted(rows, key=lambda r: r["week"])
                    seen_team[pro_team] = True
        # end fallback build (no additional code here)

    # Ensure bye week rows are present (opponent='BYE', bye=True)
    expected_weeks = 18 if year >= 2021 else 17
    for team, rows in schedule_by_team.items():
        have = {r["week"] for r in rows}
        for wk in range(1, expected_weeks + 1):
            if wk not in have:
                rows.append({
                    "week": wk,
                    "opponent": "BYE",
                    "date": None,
                    "points": None,
                    "projected_points": None,
                    "bye": True,
                })
        rows.sort(key=lambda r: r["week"])

    return schedule_by_team


def main():
    parser = argparse.ArgumentParser(description="Get NFL D/ST schedule from ESPN fantasy API")
    parser.add_argument("--year", type=int, default=datetime.now().year - 1, help="Season year (default: last year)")
    parser.add_argument("--team", type=str, default=None, help="Optional NFL team abbrev (e.g., PIT, SF) to filter")
    parser.add_argument("--json", action="store_true", help="Output JSON only")
    args = parser.parse_args()

    schedules = collect_defense_schedule(year=args.year)

    if args.team:
        team_key = args.team.upper()
        team_sched = schedules.get(team_key, [])
        if args.json:
            print(json.dumps({team_key: team_sched}, indent=2))
        else:
            print(f"Defense schedule for {team_key} in {args.year}:")
            for row in team_sched:
                bye_tag = " (BYE)" if row["bye"] else ""
                print(f"  Week {row['week']}: vs {row['opponent']} on {row['date']}{bye_tag} | pts={row['points']} proj={row['projected_points']}")
    else:
        if args.json:
            print(json.dumps(schedules, indent=2))
        else:
            for team, sched in sorted(schedules.items()):
                print(f"\nDefense schedule for {team} in {args.year}:")
                for row in sched:
                    bye_tag = " (BYE)" if row["bye"] else ""
                    print(f"  Week {row['week']}: vs {row['opponent']} on {row['date']}{bye_tag} | pts={row['points']} proj={row['projected_points']}")


if __name__ == "__main__":
    main()


