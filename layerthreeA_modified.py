import pandas as pd
import requests
from datetime import date

def fetch_layer_threeA(game_date: str) -> pd.DataFrame:
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
                "At Bats": s.get("atBats"),
                "Runs": s.get("runs"),
                "RBI": s.get("rbi"),
                "Hits": s.get("hits"),
                "Doubles": s.get("doubles"),
                "Triples": s.get("triples"),
                "Home Runs": s.get("homeRuns"),
                "Strikeouts": s.get("strikeOuts"),
                "Walks": s.get("baseOnBalls"),
                "Hit By Pitch": s.get("hitByPitch"),
                "Sac Flies": s.get("sacFlies"),
                "Sac Bunts": s.get("sacBunts"),
                "Stolen Bases": s.get("stolenBases"),
                "Caught Stealing": s.get("caughtStealing"),
                "Ground Into DP": s.get("groundIntoDoublePlay"),
                "OBP": s.get("obp"),
                "SLG": s.get("slg"),
                "OPS": s.get("ops"),
                "AVG": s.get("avg"),
                "BABIP": s.get("babip"),
                "Total Bases": s.get("totalBases"),
                "Ground Outs": s.get("groundOuts"),
                "Air Outs": s.get("airOuts"),
                "Left On Base": s.get("leftOnBase")
            })

    df = pd.DataFrame(all_rows)

    # Convert to numeric
    num_cols = [
        "Plate Appearances", "At Bats", "Hits", "Doubles", "Triples",
        "Home Runs", "Strikeouts", "Walks", "OBP", "SLG", "OPS", "AVG",
        "Ground Outs", "Air Outs", "Runs", "RBI", "Hit By Pitch",
        "Sac Flies", "Stolen Bases", "Caught Stealing", "Ground Into DP"
    ]
    df[num_cols] = df[num_cols].apply(pd.to_numeric, errors="coerce")

    # Derived metrics
    df["ISO"] = df["SLG"] - df["AVG"]
    df["K%"] = df["Strikeouts"] / df["Plate Appearances"]
    df["BB%"] = df["Walks"] / df["Plate Appearances"]
    df["XBH%"] = (df["Doubles"] + df["Triples"] + df["Home Runs"]) / df["Hits"]
    df["GB/FB"] = df["Ground Outs"] / df["Air Outs"]

    # 🔥 New metrics
    df["SB%"] = df["Stolen Bases"] / (df["Stolen Bases"] + df["Caught Stealing"])
    df["HBP%"] = df["Hit By Pitch"] / df["Plate Appearances"]
    df["SacFly%"] = df["Sac Flies"] / df["Plate Appearances"]
    df["GIDP/PA"] = df["Ground Into DP"] / df["Plate Appearances"]
    df["RBI/PA"] = df["RBI"] / df["Plate Appearances"]
    df["R/PA"] = df["Runs"] / df["Plate Appearances"]

    return df

if __name__ == "__main__":
    today = date.today().isoformat()
    df = fetch_layer_threeA(today)
    df.to_csv(f"layerthreeA_output_{today}.csv", index=False)
    print(f"✅ Output saved to layerthreeA_output_{today}.csv")
