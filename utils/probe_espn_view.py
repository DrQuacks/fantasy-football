import os
import sys
import json
import argparse
import requests

def summarize(obj, name="", max_keys=40, max_str=200, indent=0):
    pad = "  " * indent
    t = type(obj).__name__
    if isinstance(obj, dict):
        keys = list(obj.keys())
        print(f"{pad}{name} <dict> keys={len(keys)}")
        for k in keys[:max_keys]:
            v = obj[k]
            vt = type(v).__name__
            if isinstance(v, (dict, list)):
                print(f"{pad}  • {k}: <{vt}>")
            else:
                vs = repr(v)
                if len(vs) > max_str:
                    vs = vs[:max_str] + "…"
                print(f"{pad}  • {k}: {vs} <{vt}>")
        if len(keys) > max_keys:
            print(f"{pad}  … (+{len(keys)-max_keys} more keys)")
    elif isinstance(obj, list):
        print(f"{pad}{name} <list> len={len(obj)}")
        if obj:
            first = obj[0]
            ft = type(first).__name__
            if isinstance(first, dict):
                print(f"{pad}  [0] <dict> keys={len(first)} -> {list(first.keys())[:max_keys]}")
            elif isinstance(first, list):
                print(f"{pad}  [0] <list> len={len(first)}")
            else:
                vs = repr(first)
                if len(vs) > max_str:
                    vs = vs[:max_str] + "…"
                print(f"{pad}  [0] {vs} <{ft}>")
    else:
        vs = repr(obj)
        if len(vs) > max_str:
            vs = vs[:max_str] + "…"
        print(f"{pad}{name} {vs} <{t}>")

def main():
    ap = argparse.ArgumentParser(description="Probe ESPN Fantasy v3 view JSON (no parsing).")
    ap.add_argument("--league", type=int, required=True, help="League ID")
    ap.add_argument("--year", type=int, required=True, help="Season year")
    ap.add_argument("--week", type=int, default=None, help="Week (scoringPeriodId/matchupPeriodId)")
    ap.add_argument("--view", type=str, required=True, help="View name (e.g., mBoxscore, mMatchupScore, mMatchup, mRoster, mSchedule, kona_player_info)")
    ap.add_argument("--save", type=str, default=None, help="Path to save raw JSON")
    ap.add_argument("--no-cookies", action="store_true", help="Send no cookies (public leagues only)")
    args = ap.parse_args()

    swid = os.getenv("ESPN_SWID")
    s2 = os.getenv("ESPN_S2")
    if not args.no_cookies and (not swid or not s2):
        print("⚠️  Missing cookies. Set ESPN_SWID and ESPN_S2 (or use --no-cookies for a public league).")
        sys.exit(1)

    url = f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/{args.year}/segments/0/leagues/{args.league}"
    params = {"view": args.view}
    if args.week is not None:
        params["scoringPeriodId"] = args.week
        params["matchupPeriodId"] = args.week

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://fantasy.espn.com/",
        "Origin": "https://fantasy.espn.com",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "x-fantasy-source": "kona",
        "x-fantasy-platform": "kona-PROD",
    }
    cookies = {} if args.no_cookies else {"swid": swid, "espn_s2": s2}

    r = requests.get(url, params=params, headers=headers, cookies=cookies, timeout=25)
    ct = r.headers.get("Content-Type", "")
    print(f"HTTP {r.status_code} | Content-Type: {ct} | URL: {r.url}")

    if r.status_code != 200:
        print(r.text[:400])
        r.raise_for_status()

    # Try JSON; if HTML, show first lines and exit
    try:
        data = r.json()
    except Exception:
        txt = r.text[:400]
        print("⚠️  Non-JSON body (showing first 400 chars):")
        print(txt)
        sys.exit(2)

    # Save raw if asked
    if args.save:
        with open(args.save, "w") as f:
            json.dump(data, f, indent=2)
        print(f"💾 Saved JSON to {args.save}")

    # Summarize top-level
    if isinstance(data, dict):
        print("\n=== Top-level dict ===")
        summarize(data, name="root", indent=0)
        # Show common arrays if present
        for key in ("schedule", "teams", "draftDetail", "members", "players", "gameId"):
            if key in data:
                print(f"\n=== Peek: {key} ===")
                summarize(data[key], name=key, indent=0)
    elif isinstance(data, list):
        print("\n=== Top-level list ===")
        summarize(data, name="root", indent=0)
        if data and isinstance(data[0], dict):
            print("\n=== Peek first item ===")
            summarize(data[0], name="root[0]", indent=0)
    else:
        summarize(data, name="root", indent=0)

if __name__ == "__main__":
    main()
