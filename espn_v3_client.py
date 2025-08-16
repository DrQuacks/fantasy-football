# espn_v3_client.py
import os
import json
import time
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional, Union, List, Tuple

import requests

BASE = "https://fantasy.espn.com/apis/v3/games/ffl/seasons/{year}/segments/0/leagues/{league_id}"
CACHE_DIR = Path(".cache/espn_v3")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

class ESPNV3Client:
    def __init__(
        self,
        league_id: Union[int, str],
        year: int,
        swid: Optional[str] = None,
        espn_s2: Optional[str] = None,
        session: Optional[requests.Session] = None,
        use_cache: bool = True,
        retries: int = 3,
        backoff: float = 0.8,
        timeout: float = 20.0,
    ):
        """
        Minimal client for ESPN Fantasy Football v3 endpoints.
        """
        self.league_id = str(league_id)
        self.year = int(year)
        self.use_cache = use_cache
        self.retries = retries
        self.backoff = backoff
        self.timeout = timeout

        self.session = session or requests.Session()
        self.cookies = {}
        # Allow cookies via env or args
        swid = swid or os.getenv("ESPN_SWID")
        espn_s2 = espn_s2 or os.getenv("ESPN_S2")
        self.default_headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://fantasy.espn.com/",
            "Origin": "https://fantasy.espn.com",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            # ESPN “kona” layer hints:
            "x-fantasy-source": "kona",
            "x-fantasy-platform": "kona-PROD",
}
        if swid and espn_s2:
            self.cookies = {"swid": swid, "espn_s2": espn_s2}

    # ---------------------------
    # Internal helpers
    # ---------------------------
    def _league_url(self) -> str:
        return BASE.format(year=self.year, league_id=self.league_id)

    def _cache_key(self, url: str, params: Dict[str, Any], xff: Optional[Dict[str, Any]]) -> Path:
        key_src = {"url": url, "params": params, "xff": xff}
        digest = hashlib.sha256(json.dumps(key_src, sort_keys=True).encode()).hexdigest()
        return CACHE_DIR / f"{digest}.json"

    
    def _request_json(self, url: str, params: dict, x_fantasy_filter: Optional[dict] = None):
        # default headers (UA + Referer + Accept)
        headers = dict(getattr(self, "default_headers", {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://fantasy.espn.com/",
        }))
        if x_fantasy_filter is not None:
            headers["x-fantasy-filter"] = json.dumps(x_fantasy_filter)
        headers.setdefault("Accept", "application/json, text/plain, */*")

        # make sure cache dir exists
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

        cache_path = self._cache_key(url, params, x_fantasy_filter)
        if self.use_cache and cache_path.exists():
            with cache_path.open("r") as f:
                return json.load(f)

        last_err = None
        for attempt in range(1, self.retries + 1):
            try:
                r = self.session.get(
                    url,
                    params=params,
                    cookies=self.cookies,
                    headers=headers,
                    timeout=self.timeout,
                )
                ct = r.headers.get("Content-Type", "")

                if r.status_code in (401, 403):
                    snippet = r.text[:300].replace("\n", " ")
                    raise requests.HTTPError(
                        f"Auth error {r.status_code}. CT={ct}. "
                        f"Params={params}. Body starts: {snippet}"
                    )

                if r.status_code >= 500:
                    raise requests.HTTPError(f"{r.status_code} server error from ESPN")

                r.raise_for_status()

                try:
                    data = r.json()
                except Exception as je:
                    # ensure the debug file path exists
                    dbg = CACHE_DIR / "last_nonjson_response.txt"
                    try:
                        dbg.parent.mkdir(parents=True, exist_ok=True)
                        dbg.write_bytes(r.content[:4000])
                    except Exception as we:
                        # fall back to printing a small snippet
                        print("⚠️ Could not write debug file:", we)
                        print("First 300 chars of body:", r.text[:300])

                    raise requests.HTTPError(
                        f"Non-JSON response (status {r.status_code}, CT={ct}). "
                        f"Wrote body preview to {dbg}. Params={params}"
                    ) from je

                if self.use_cache:
                    with cache_path.open("w") as f:
                        json.dump(data, f)
                return data

            except Exception as e:
                last_err = e
                if attempt < self.retries:
                    time.sleep(self.backoff * attempt)
                else:
                    raise
        raise last_err

    # ---------------------------
    # Public endpoints
    # ---------------------------
    def get_schedule(self, matchup_period: Optional[int] = None) -> Any:
        """
        League schedule. Add matchup_period to focus on a week.
        """
        url = self._league_url()
        params = {"view": "mSchedule"}
        if matchup_period is not None:
            params["matchupPeriodId"] = int(matchup_period)
        return self._request_json(url, params)

    def get_boxscores(self, week: int):
        url = self._league_url()
        # Try in this order; many leagues succeed on mMatchupScore
        candidates = [
            {"view": "mBoxscore", "scoringPeriodId": int(week), "matchupPeriodId": int(week)},
            {"view": "mMatchupScore", "scoringPeriodId": int(week), "matchupPeriodId": int(week)},
            {"view": "mMatchup", "scoringPeriodId": int(week), "matchupPeriodId": int(week)},
        ]
        last_err = None
        for params in candidates:
            try:
                return self._request_json(url, params)
            except Exception as e:
                last_err = e
                # keep trying next view
        # if all failed:
        raise last_err

    def get_rosters(self, week: Optional[int] = None) -> Any:
        """
        Fantasy rosters. If week is provided, use scoringPeriodId.
        """
        url = self._league_url()
        params = {"view": "mRoster"}
        if week is not None:
            params["scoringPeriodId"] = int(week)
        return self._request_json(url, params)

    def get_teams(self) -> Any:
        """
        Fantasy teams metadata.
        """
        url = self._league_url()
        params = {"view": "mTeam"}
        return self._request_json(url, params)

    def get_players_kona(
        self,
        week: Optional[int] = None,
        player_ids: Optional[List[int]] = None,
        positions: Optional[List[str]] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Any:
        """
        League-scoped player info (kona_player_info). Supports filters via x-fantasy-filter.
        - player_ids: filterIds
        - positions: e.g. ["QB","RB","WR","TE","K","D/ST"] (exact tokens can vary; you may map to ESPN's internal codes)
        - status: e.g. "FREEAGENT", "WAIVERS", "ONTEAM" (varies by season)
        - limit/offset: sometimes honored; depends on season/endpoint behavior
        """
        url = self._league_url()
        params = {"view": "kona_player_info"}
        if week is not None:
            params["scoringPeriodId"] = int(week)

        # Build x-fantasy-filter
        xff: Dict[str, Any] = {"players": {}}
        if player_ids:
            xff["players"]["filterIds"] = {"value": player_ids}
        if positions:
            xff["players"]["filterSlotIds"] = {"value": positions}  # beware: might need slot IDs; adjust as needed
        if status:
            xff["players"]["filterStatus"] = {"value": [status]}
        if limit is not None:
            xff["players"]["limit"] = limit
        if offset is not None:
            xff["players"]["offset"] = offset

        return self._request_json(url, params, x_fantasy_filter=xff)

    def get_players_catalog_paged(
        self,
        year: Optional[int] = None,
        limit: int = 50,
        start: int = 0,
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Any, Dict[str, Any]]:
        """
        Example of a global-style players catalog (varies by season).
        Some seasons expose a league-scoped variant only; this method is here
        as a placeholder if you discover the global players endpoint in DevTools.
        Returns (json, used_params).
        """
        # You’ll likely discover the exact URL in devtools (Network tab)
        # when browsing players in the web UI. Keep this as a scratch pad.
        base_players = f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/{year or self.year}/players"
        params = {"limit": limit, "offset": start}
        if extra_params:
            params.update(extra_params)
        data = self._request_json(base_players, params)
        return data, params
