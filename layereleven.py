# layer11.py

import pandas as pd
import numpy as np
from pybaseball import statcast, playerid_reverse_lookup
from datetime import datetime, timedelta

def fetch_layer_eleven(game_date: str) -> pd.DataFrame:
    """
    Fetches pitcher-batter matchups over the past 365 days leading up to game_date,
    aggregates outcomes, calculates metrics, and attaches player names.
    :param game_date: "YYYY-MM-DD"; determines end date for the 365-day window.
    :return: DataFrame with columns:
      ['BatterName','PitcherName','batter','pitcher','PA','Hits','HR','BB','K',
       'AVG','OBP','SLG','OPS','ISO','K%','BB%']
    """
    # 1) Determine date range
    end_dt = datetime.strptime(game_date, "%Y-%m-%d")
    start_dt = end_dt - timedelta(days=365)

    # 2) Pull raw Statcast data
    raw = statcast(
        start_dt=start_dt.strftime("%Y-%m-%d"),
        end_dt=end_dt.strftime("%Y-%m-%d")
    )
    if raw.empty:
        return pd.DataFrame()

    # 3) Filter and flag outcomes
    df = raw.dropna(subset=["batter", "pitcher", "description"]).copy()
    df["is_hit"] = df["events"].isin(["single", "double", "triple", "home_run"])
    df["is_hr"]  = df["events"] == "home_run"
    df["is_bb"]  = df["description"].str.contains("walk", na=False)
    df["is_k"]   = df["description"].str.contains("strikeout", na=False)

    # 4) Aggregate per batter-pitcher pair
    summary = (
        df.groupby(["batter", "pitcher"])
          .agg(
            PA=("pitch_type", "count"),
            Hits=("is_hit", "sum"),
            HR=("is_hr", "sum"),
            BB=("is_bb", "sum"),
            K=("is_k", "sum")
          )
          .reset_index()
    )

    if summary.empty:
        return pd.DataFrame()

    # 5) Calculate metrics
    summary["AVG"]  = summary["Hits"] / summary["PA"]
    summary["OBP"]  = (summary["Hits"] + summary["BB"]) / summary["PA"]
    summary["SLG"]  = (summary["Hits"] + 2 * summary["HR"]) / summary["PA"]
    summary["OPS"]  = summary["OBP"] + summary["SLG"]
    summary["ISO"]  = summary["SLG"] - summary["AVG"]
    summary["K%"]   = summary["K"] / summary["PA"]
    summary["BB%"]  = summary["BB"] / summary["PA"]

    # 6) Clean infinities
    summary.replace([np.inf, -np.inf], np.nan, inplace=True)

    # 7) Lookup full player names
    ids = pd.unique(summary[["batter", "pitcher"]].values.ravel())
    lookup = playerid_reverse_lookup(ids, key_type="mlbam")
    lookup["full_name"] = lookup["name_first"] + " " + lookup["name_last"]
    lookup = lookup[["key_mlbam", "full_name"]].rename(
        columns={"key_mlbam": "player_id", "full_name": "full_name"}
    )

    # 8) Merge names
    summary = summary.merge(
        lookup.rename(columns={"player_id": "batter", "full_name": "BatterName"}),
        on="batter", how="left"
    )
    summary = summary.merge(
        lookup.rename(columns={"player_id": "pitcher", "full_name": "PitcherName"}),
        on="pitcher", how="left"
    )

    # 9) Reorder and round
    cols = [
        "BatterName", "PitcherName", "batter", "pitcher",
        "PA", "Hits", "HR", "BB", "K",
        "AVG", "OBP", "SLG", "OPS", "ISO", "K%", "BB%"
    ]
    summary = summary[cols]
    summary[["AVG", "OBP", "SLG", "OPS", "ISO", "K%", "BB%"]] = \
        summary[["AVG", "OBP", "SLG", "OPS", "ISO", "K%", "BB%"]].round(3)

    return summary
