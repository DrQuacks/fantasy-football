from pymongo import MongoClient, UpdateOne
from tqdm import tqdm
from typing import Dict, Tuple
from defense_schedule import collect_defense_schedule


ABBREV_ALIASES = {
    "JAC": "JAX", "JAX": "JAX",
    "WAS": "WSH", "WSH": "WSH",
    "LA": "LAR", "RAM": "LAR", "LAR": "LAR",
    "SD": "LAC", "LAC": "LAC",
    "OAK": "LV", "LV": "LV",
    "NOR": "NO", "NO": "NO",
    "GNB": "GB", "GB": "GB",
    "KAN": "KC", "KC": "KC",
    "SFO": "SF", "SF": "SF",
    "NWE": "NE", "NE": "NE",
    "TAM": "TB", "TB": "TB",
    "ARZ": "ARI", "ARI": "ARI",
    "BLT": "BAL", "BAL": "BAL",
    "CLV": "CLE", "CLE": "CLE",
}


def norm(abbr: str) -> str:
    if not abbr:
        return abbr
    a = abbr.strip().upper()
    return ABBREV_ALIASES.get(a, a)


def build_week_opp_to_team_map(year: int) -> Dict[Tuple[int, str], str]:
    """
    From the defense schedules, build a mapping: (week, opponent) -> defense_team.
    This lets us infer a player's team given the opponent and week.
    """
    schedules = collect_defense_schedule(year=year)
    mapping: Dict[Tuple[int, str], str] = {}
    for defense_team, rows in schedules.items():
        team_abbr = norm(defense_team)
        for r in rows:
            wk = int(r.get("week"))
            opp = norm(r.get("opponent"))
            if not wk or not opp:
                continue
            mapping[(wk, opp)] = team_abbr
    return mapping


def backfill_player_team(mongo_uri: str = "mongodb://localhost:27017/", first_year: int = 2019, last_year: int = 2024):
    client = MongoClient(mongo_uri)
    db = client["fantasy_football"]
    collection = db["player_stats"]

    for year in range(first_year, last_year + 1):
        print(f"\n📅 Building defense-derived map for {year}...")
        week_opp_to_team = build_week_opp_to_team_map(year)
        print(f"  Map size: {len(week_opp_to_team)} entries")

        ops = []
        total_matched = 0
        total_seen = 0
        cursor = collection.find({"year": year}, {"_id": 1, "weekly_stats": 1})
        for doc in tqdm(cursor, desc=f"Backfilling player_team via defense schedule {year}"):
            weekly_stats = doc.get("weekly_stats", {}) or {}
            if not weekly_stats:
                continue
            set_updates = {}
            for week_str, wk in weekly_stats.items():
                try:
                    week = int(week_str)
                except Exception:
                    continue
                if week == 0:
                    continue
                opp_raw = (wk or {}).get("team")  # opponent already stored under 'team'
                opp = norm(opp_raw)
                if not opp:
                    continue
                total_seen += 1
                team_abbr = week_opp_to_team.get((week, opp))
                if team_abbr:
                    set_updates[f"weekly_stats.{week_str}.player_team"] = team_abbr
                    total_matched += 1
                # Also set bye flag if defense schedule indicates BYE for that team-week
                if opp == "BYE":
                    set_updates[f"weekly_stats.{week_str}.bye_week"] = True
            if set_updates:
                ops.append(UpdateOne({"_id": doc["_id"]}, {"$set": set_updates}))

        if ops:
            result = collection.bulk_write(ops, ordered=False)
            print(f"✅ {year}: modified={result.modified_count}, matched_rows={total_matched}/{total_seen}")
        else:
            print(f"⚠️ {year}: no updates | matched_rows={total_matched}/{total_seen}")


if __name__ == "__main__":
    backfill_player_team()


