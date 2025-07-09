# layerten_modified.py

import pandas as pd
import requests
from typing import List

def fetch_layer_ten(game_date: str) -> pd.DataFrame:
    """
    Pulls all MLB team seasonal platoon splits vs LHP and RHP from 2019–2025.
    Adds every available stat from the endpoint.
    """
    seasons: List[int] = list(range(2019, 2026))
    records = []

    teams = requests.get("https://statsapi.mlb.com/api/v1/teams", params={"sportId": 1}, timeout=20).json()['teams']
    stats_url = "https://statsapi.mlb.com/api/v1/stats"

    for season in seasons:
        for team in teams:
            team_id = team['id']
            team_name = team['name']

            for split in ("vsLHP", "vsRHP"):
                params = {
                    "stats": "season",
                    "group": "hitting",
                    "season": season,
                    "teamId": team_id,
                    "sportId": 1,
                    "split": split,
                    "gameType": "R"
                }
                r = requests.get(stats_url, params=params, timeout=15)
                if r.status_code != 200:
                    continue

                stats = r.json().get("stats", [])
                if not stats or not stats[0]['splits']:
                    continue

                stat = stats[0]['splits'][0]['stat']
                pa = int(stat.get('plateAppearances', 0))
                if pa == 0:
                    continue

                row = {
                    "Team": team_name,
                    "Season": season,
                    "Split": split,
                    "PA": pa,
                    "AB": int(stat.get("atBats", 0)),
                    "H": int(stat.get("hits", 0)),
                    "2B": int(stat.get("doubles", 0)),
                    "3B": int(stat.get("triples", 0)),
                    "HR": int(stat.get("homeRuns", 0)),
                    "R": int(stat.get("runs", 0)),
                    "RBI": int(stat.get("rbi", 0)),
                    "BB": int(stat.get("baseOnBalls", 0)),
                    "SO": int(stat.get("strikeOuts", 0)),
                    "HBP": int(stat.get("hitByPitch", 0)),
                    "SB": int(stat.get("stolenBases", 0)),
                    "CS": int(stat.get("caughtStealing", 0)),
                    "GIDP": int(stat.get("groundIntoDoublePlay", 0)),
                    "XBH": int(stat.get("extraBaseHits", 0)),
                    "TB": int(stat.get("totalBases", 0)),
                    "TOB": int(stat.get("timesOnBase", 0)),
                    "LOB": int(stat.get("leftOnBase", 0)),
                    "GO": int(stat.get("groundOuts", 0)),
                    "AO": int(stat.get("airOuts", 0)),
                    "AVG": float(stat.get("avg", 0)),
                    "OBP": float(stat.get("obp", 0)),
                    "SLG": float(stat.get("slg", 0)),
                    "OPS": float(stat.get("ops", 0)),
                    "BABIP": float(stat.get("babip", 0)),
                    "P/PA": float(stat.get("pitchesPerPlateAppearance", 0)),
                    "BB/K": float(stat.get("walksPerStrikeout", 0)),
                }

                # Derived stats
                row["K%"] = row["SO"] / pa
                row["BB%"] = row["BB"] / pa
                row["ISO"] = row["SLG"] - row["AVG"]

                records.append(row)

    return pd.DataFrame(records)

if __name__ == '__main__':
    from datetime import datetime
    today = datetime.today().strftime('%Y-%m-%d')
    df = fetch_layer_ten(today)
    df.to_csv(f'layerten_output_{today}.csv', index=False)
    print(f"✅ Output saved: layerten_output_{today}.csv")
