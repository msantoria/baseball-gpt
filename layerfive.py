# layerfive.py

import pandas as pd
from pybaseball import statcast
from datetime import datetime, timedelta

def fetch_layer_five(game_date: str) -> pd.DataFrame:
    """
    Fetches FULL team‐level batting Statcast events for the past 1000 days,
    computes batted‐ball flags and rates, and returns a clean DataFrame with:
      ['Team','Avg EV','Max EV','Avg LA','xwOBA','Barrel %',
       'Hard Hit %','K %','BB %']
    The game_date parameter is ignored; we always look back 1000 days from today.
    """
    # 1) Date range (1000 days back from today)
    end_dt = datetime.today()
    start_dt = end_dt - timedelta(days=1000)
    start_str = start_dt.strftime('%Y-%m-%d')
    end_str   = end_dt.strftime('%Y-%m-%d')

    print(f"🔁 Pulling team batting Statcast data from {start_str} to {end_str}...")

    # 2) Pull raw events
    raw = statcast(start_dt=start_str, end_dt=end_str)

    # 3) Filter for true plate appearances
    raw = raw[raw['batter'].notna() & raw['description'].notna()]

    # 4) Ensure necessary columns exist
    for col in ('launch_speed','launch_angle','estimated_woba_using_speedangle','description'):
        if col not in raw.columns:
            raw[col] = pd.NA

    # 5) Derive batted‐ball flags
    raw['launch_speed'] = pd.to_numeric(raw['launch_speed'], errors='coerce')
    raw['launch_angle'] = pd.to_numeric(raw['launch_angle'], errors='coerce')
    raw['hard_hit']   = (raw['launch_speed'] >= 95).fillna(False).astype(int)
    raw['sweet_spot'] = raw['launch_angle'].between(8, 32).fillna(False).astype(int)
    raw['ground_ball']= (raw['launch_angle'] < 10).fillna(False).astype(int)
    raw['fly_ball']   = (raw['launch_angle'] > 25).fillna(False).astype(int)
    raw['line_drive'] = raw['launch_angle'].between(10, 25).fillna(False).astype(int)
    raw['popup']      = (raw['launch_angle'] > 50).fillna(False).astype(int)
    raw['strikeout']  = raw['description'].str.contains("strikeout", na=False).astype(int)
    raw['walk']       = raw['description'].str.contains("walk", na=False).astype(int)
    raw['barrel'] = (
        (raw['launch_speed'] >= 98) &
        raw['launch_angle'].between(26, 30)
    ).fillna(False).astype(int)
    raw['PA'] = 1

    # 6) Aggregate by team
    grouped = raw.groupby('home_team').agg({
        'launch_speed': ['mean','max'],
        'launch_angle': 'mean',
        'estimated_woba_using_speedangle': 'mean',
        'barrel': 'sum',
        'hard_hit': 'sum',
        'strikeout': 'sum',
        'walk': 'sum',
        'PA': 'sum'
    })
    # flatten columns
    grouped.columns = [
        'Avg EV','Max EV','Avg LA','xwOBA',
        'Barrels','Hard Hits','Strikeouts','Walks','PAs'
    ]
    df = grouped.reset_index().rename(columns={'home_team': 'Team'})

    # 7) Compute rates
    df['Barrel %']   = df['Barrels']    / df['PAs'] * 100
    df['Hard Hit %'] = df['Hard Hits']  / df['PAs'] * 100
    df['K %']        = df['Strikeouts'] / df['PAs'] * 100
    df['BB %']       = df['Walks']      / df['PAs'] * 100

    # 8) Select final columns
    final_df = df[[
        'Team','Avg EV','Max EV','Avg LA','xwOBA',
        'Barrel %','Hard Hit %','K %','BB %'
    ]]

    return final_df
