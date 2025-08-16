# probe_raw.py
import os, sys, json, argparse, requests

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--league", type=int, required=True)
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--view", type=str, required=True)
    ap.add_argument("--week", type=int, default=None)
    ap.add_argument("--save", help="Optional file path to save the raw JSON response")
    args = ap.parse_args()

    swid = os.getenv("ESPN_SWID")
    s2   = os.getenv("ESPN_S2")
    if not swid or not s2:
        print("Missing cookies. export ESPN_SWID and ESPN_S2 first.")
        sys.exit(1)

    url = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{args.year}/segments/0/leagues/{args.league}"
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
    cookies = {"swid": swid, "espn_s2": s2}

    # DO NOT FOLLOW REDIRECTS – we want to see if ESPN is bouncing us
    cookie_header = f"swid={os.getenv('ESPN_SWID')}; espn_s2={os.getenv('ESPN_S2')}"
    r = requests.get(
        url,
        params=params,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://fantasy.espn.com/",
            "Origin": "https://fantasy.espn.com",
            "Accept": "application/json, text/plain, */*",
            "x-fantasy-source": "kona",
            "x-fantasy-platform": "kona-PROD",
            "Cookie": cookie_header,          # 👈 raw cookie header
        },
        timeout=25,
        allow_redirects=False
    )
    print("HTTP", r.status_code, "| CT:", r.headers.get("Content-Type"))
    print("URL:", r.url)
    print("Location:", r.headers.get("Location"))
    print("Body first 120:", r.text[:120])

    if r.status_code != 200:
        print("Body (first 400 chars):")
        print(r.text[:400])
        sys.exit(2)

    # Try to parse JSON; if it fails, print the first bit of HTML/text and stop.
    try:
        data = r.json()

        if args.save:
            import json
            with open(args.save, "w") as f:
                json.dump(data, f, indent=2)
            print(f"💾 Saved raw JSON to {args.save}")

        print("Top-level keys:", list(data.keys()))
    except Exception:
        print("Non-JSON body (first 400 chars):")
        print(r.text[:400])
        sys.exit(3)

    # If JSON, print top-level keys and exit.
    if isinstance(data, dict):
        print("Top-level keys:", list(data.keys())[:40])
    elif isinstance(data, list):
        print(f"Top-level is a list (len={len(data)})")
        if data and isinstance(data[0], dict):
            print("First item keys:", list(data[0].keys())[:40])
    else:
        print("Top-level JSON type:", type(data).__name__)

if __name__ == "__main__":
    main()
