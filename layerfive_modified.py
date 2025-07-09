import pandas as pd
import requests
from datetime import date

def fetch_layer_five(game_date: str) -> pd.DataFrame:
    seasons = [2021, 2022, 2023, 2024, 2025]
    all_rows = []

    for season in seasons:
        url = (
            "https://statsapi.mlb.com/api/v1/stats"
            "?stats=season&group=hitting&gameType=R&limit=1000"
            f"&season={season}"
        )
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        splits = data.get("stats", [{}])[0].get("splits", [])
        for split in splits:
            s = split["stat"]
            all_rows.append({
                "Season": season,
                "Team": split["team"]["name"],
                "Plate Appearances": s.get("plateAppearances"),
                "Hits": s.get("hits"),
                "Ground Outs": s.get("groundOuts"),
                "Air Outs": s.get("airOuts"),
                "Extra Base Hits": s.get("extraBaseHits"),
                "Strikeouts": s.get("strikeOuts"),
                "Walks": s.get("baseOnBalls"),
                "Hit By Pitch": s.get("hitByPitch"),
                "Stolen Bases": s.get("stolenBases"),
                "Caught Stealing": s.get("caughtStealing")
            })

    df = pd.DataFrame(all_rows)

    # Convert all to numeric
    num_cols = [
        "Plate Appearances", "Hits", "Ground Outs", "Air Outs",
        "Extra Base Hits", "Strikeouts", "Walks",
        "Hit By Pitch", "Stolen Bases", "Caught Stealing"
    ]
    df[num_cols] = df[num_cols].apply(pd.to_numeric, errors="coerce")

    # Derived metrics
    df["GB/FB"] = df["Ground Outs"] / df["Air Outs"]
    df["SB%"] = df["Stolen Bases"] / (df["Stolen Bases"] + df["Caught Stealing"])

    return df

if __name__ == "__main__":
    today = date.today().isoformat()
    df = fetch_layer_five(today)
    df.to_csv(f"layerfive_output_{today}.csv", index=False)
    print(f"✅ Output saved to layerfive_output_{today}.csv")
