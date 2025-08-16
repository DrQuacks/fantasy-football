#!/usr/bin/env python3
"""
augment_weekly_team_opponent.py

Enrich Mongo weekly_stats with:
  - nfl_team    (ESPN team abbrev for that week)
  - nfl_opponent
  - isHome      (True if 'atVs' != '@')

Data source: ESPN public gamelog
  https://site.web.api.espn.com/apis/common/v3/sports/football/nfl/athletes/{athlete_id}/gamelog
  params: season=<year>, seasontype=2 (regular season)

Rules:
- Skip any event with 'eventNote' (playoffs or special).
- Use event['week'] to map to Mongo weekly_stats keys.
- Only update existing weeks (do NOT create new weeks).
- Only process positive playerId values (skip defenses / non-athletes with negative IDs).
- Write a human-readable report of failures/skips to a .md (or .txt) file.

Safe to re-run: subsequent runs simply overwrite those 3 fields for each week.
"""

import os
import time
import json
import argparse
import logging
from typing import Dict, Any, List, Tuple, Optional

import requests
from pymongo import MongoClient, UpdateOne
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ---------- Defaults ----------
DEFAULT_MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DEFAULT_DB_NAME   = os.getenv("MONGO_DB", "fantasy_football")
DEFAULT_COLL_NAME = os.getenv("MONGO_COLL", "player_stats")

ESPN_GAMES_URL = "https://site.web.api.espn.com/apis/common/v3/sports/football/nfl/athletes/{athlete_id}/gamelog"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17 Safari/605.1.15"

# ---------- Logging ----------
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("augment")


def build_session() -> requests.Session:
    """Requests session with retries/backoff."""
    s = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=0.6,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET"]),
        raise_on_status=False,
    )
    s.mount("https://", HTTPAdapter(max_retries=retries))
    s.headers.update({"User-Agent": USER_AGENT})
    return s


def fetch_gamelog(session: requests.Session, athlete_id: int, season: int, seasontype: int = 2) -> Optional[Dict[str, Any]]:
    """Fetch ESPN gamelog JSON for a player; return dict or None on failure."""
    url = ESPN_GAMES_URL.format(athlete_id=athlete_id)
    try:
        r = session.get(url, params={"season": season, "seasontype": seasontype}, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        log.warning(f"Fetch failed for player {athlete_id} {season}: {e}")
        return None


def iter_events(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Normalize response to a list of event dicts."""
    events = data.get("events")
    if isinstance(events, dict):
        return list(events.values())
    if isinstance(events, list):
        return events
    return []


def extract_week_info(event: Dict[str, Any]) -> Optional[Tuple[int, str, str, bool]]:
    """
    Return (week, nfl_team, nfl_opponent, isHome) or None.
    Skip if 'eventNote' present (playoffs).
    """
    if "eventNote" in event:
        return None

    # Week number
    week = event.get("week")
    try:
        week_int = int(week)
    except (TypeError, ValueError):
        return None

    # NFL team & opponent abbreviations
    team_abbr = (event.get("team") or {}).get("abbreviation") or (event.get("team") or {}).get("shortDisplayName")
    opp_abbr  = (event.get("opponent") or {}).get("abbreviation") or (event.get("opponent") or {}).get("shortDisplayName")
    if not team_abbr or not opp_abbr:
        return None

    # Home/away from atVs ("vs" => home, "@" => away). Default to False if unknown.
    at_vs = event.get("atVs")
    is_home = (isinstance(at_vs, str) and at_vs.strip() != "@")

    return (week_int, str(team_abbr), str(opp_abbr), bool(is_home))


def main():
    ap = argparse.ArgumentParser(description="Enrich Mongo weekly_stats with NFL team/opponent/isHome via ESPN gamelog")
    ap.add_argument("--mongo", default=DEFAULT_MONGO_URI, help="Mongo URI")
    ap.add_argument("--db", default=DEFAULT_DB_NAME, help="Mongo database name")
    ap.add_argument("--coll", default=DEFAULT_COLL_NAME, help="Mongo collection name")
    ap.add_argument("--start-year", type=int, default=2019, help="Min season to process")
    ap.add_argument("--end-year", type=int, default=2024, help="Max season to process")
    ap.add_argument("--rate-delay", type=float, default=0.35, help="Sleep seconds between API calls")
    ap.add_argument("--batch", type=int, default=500, help="Bulk write batch size")
    ap.add_argument("--report-path", default="augment_failures.md", help="Path to write a report of failures/skips")
    args = ap.parse_args()

    # Mongo
    client = MongoClient(args.mongo)
    col = client[args.db][args.coll]

    session = build_session()

    # Only REAL players (athletes): positive IDs
    query = {
        "playerId": {"$exists": True, "$gt": 0},
        "year": {"$gte": args.start_year, "$lte": args.end_year},
    }
    projection = {"_id": 1, "playerId": 1, "year": 1, "name": 1, "weekly_stats": 1}
    cursor = col.find(query, projection=projection)

    # Reporting buckets
    failures: List[str] = []
    skips: List[str] = []
    empty_events: List[str] = []
    no_matching_weeks: List[str] = []

    ops: List[UpdateOne] = []
    processed = updated = 0

    try:
        for doc in cursor:
            processed += 1
            pid = doc.get("playerId")
            year = int(doc.get("year"))
            name = doc.get("name", "")
            weekly = doc.get("weekly_stats") or {}

            # Guard (double-check): positive integer ids only
            if not isinstance(pid, int) or pid <= 0:
                skips.append(f"{name} ({pid}) {year}: non-athlete or invalid id")
                continue

            data = fetch_gamelog(session, athlete_id=pid, season=year, seasontype=2)
            if not data:
                failures.append(f"{name} ({pid}) {year}: fetch failed or non-JSON")
                time.sleep(args.rate_delay)
                continue

            events = iter_events(data)
            if not events:
                empty_events.append(f"{name} ({pid}) {year}: no events returned")
                time.sleep(args.rate_delay)
                continue

            set_updates: Dict[str, Any] = {}
            matched_any = False

            for ev in events:
                info = extract_week_info(ev)
                if not info:
                    continue
                week_int, team, opp, is_home = info
                wk = str(week_int)

                if wk in weekly:
                    prefix = f"weekly_stats.{wk}"
                    set_updates[f"{prefix}.nfl_team"] = team
                    set_updates[f"{prefix}.nfl_opponent"] = opp
                    set_updates[f"{prefix}.isHome"] = is_home
                    matched_any = True

            if matched_any:
                ops.append(UpdateOne({"_id": doc["_id"]}, {"$set": set_updates}))
                updated += 1
            else:
                no_matching_weeks.append(f"{name} ({pid}) {year}: gamelog had no regular-season weeks that matched existing weekly_stats keys")

            # bulk write in batches
            if len(ops) >= args.batch:
                col.bulk_write(ops, ordered=False)
                ops.clear()

            time.sleep(args.rate_delay)

        # flush remaining
        if ops:
            col.bulk_write(ops, ordered=False)
            ops.clear()

    finally:
        client.close()

    # Write a clean report
    lines = []
    lines.append("# Augment Weekly Team/Opponent Report\n")
    lines.append(f"- Years processed: {args.start_year}–{args.end_year}")
    lines.append(f"- Mongo collection: {args.db}.{args.coll}")
    lines.append(f"- Documents scanned: {processed}")
    lines.append(f"- Documents updated: {updated}\n")

    if failures:
        lines.append("## Fetch/Parse Failures\n")
        for x in failures:
            lines.append(f"- {x}")
        lines.append("")
    else:
        lines.append("## Fetch/Parse Failures\n- None\n")

    if empty_events:
        lines.append("## Empty Events (no gamelog items)\n")
        for x in empty_events:
            lines.append(f"- {x}")
        lines.append("")
    else:
        lines.append("## Empty Events (no gamelog items)\n- None\n")

    if no_matching_weeks:
        lines.append("## No Matching Weeks\n")
        lines.append("_(Gamelog had regular-season events, but none matched existing weekly_stats keys in Mongo.)_\n")
        for x in no_matching_weeks:
            lines.append(f"- {x}")
        lines.append("")
    else:
        lines.append("## No Matching Weeks\n- None\n")

    if skips:
        lines.append("## Skipped (non-athlete or invalid ID)\n")
        for x in skips:
            lines.append(f"- {x}")
        lines.append("")
    else:
        lines.append("## Skipped (non-athlete or invalid ID)\n- None\n")

    with open(args.report_path, "w") as f:
        f.write("\n".join(lines))

    log.info(f"Processed docs: {processed}")
    log.info(f"Updated docs:   {updated}")
    log.info(f"Report written: {args.report_path}")
    log.info("Done ✅")


if __name__ == "__main__":
    main()
