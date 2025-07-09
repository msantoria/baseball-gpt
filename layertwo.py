# baseball_data/layertwo.py

import pandas as pd
import glob
import os

def fetch_layer_two() -> pd.DataFrame:
    """
    Loads all pitch-arsenal CSV files from your OneDrive Documents folder,
    concatenates them, normalizes pitcher names, and returns aggregated
    career arsenal stats.
    """
    # 1) Find all matching CSVs
    folder = r"C:\Users\micha\OneDrive\Documents"
    pattern = os.path.join(folder, "pitch-arsenal-stats (2)*.csv")
    paths = glob.glob(pattern)
    if not paths:
        raise FileNotFoundError(f"No files found matching {pattern}")

    # 2) Read and combine
    dfs = [pd.read_csv(p) for p in paths]
    arsenal_df = pd.concat(dfs, ignore_index=True)

    # 3) Normalize pitcher names
    #    original column is "last_name, first_name"
    arsenal_df['pitcher_name'] = (
        arsenal_df['last_name, first_name']
          .str.split(', ')
          .apply(lambda parts: f"{parts[1]} {parts[0]}" if len(parts)==2 else parts[0])
    )

    # 4) Select & rename relevant columns
    summary = arsenal_df[[
        'pitcher_name', 'player_id', 'pitch_type', 'pitch_name',
        'pitches', 'pitch_usage', 'whiff_percent', 'k_percent',
        'run_value_per_100', 'est_woba', 'hard_hit_percent'
    ]].copy()

    summary.rename(columns={
        'pitcher_name':    'Pitcher Name',
        'player_id':       'Player ID',
        'pitch_type':      'Pitch Type',
        'pitch_name':      'Pitch Name',
        'pitches':         'Pitch Count',
        'pitch_usage':     'Usage %',
        'whiff_percent':   'Whiff %',
        'k_percent':       'K %',
        'run_value_per_100':'RV/100',
        'est_woba':        'xwOBA',
        'hard_hit_percent':'Hard Hit %'
    }, inplace=True)

    # 5) Aggregate career stats
    career_arsenal = (
        summary
          .groupby(['Pitcher Name','Player ID','Pitch Type','Pitch Name'], as_index=False)
          .agg({
              'Pitch Count': 'sum',
              'Usage %':     'mean',
              'Whiff %':     'mean',
              'K %':         'mean',
              'RV/100':      'mean',
              'xwOBA':       'mean',
              'Hard Hit %':  'mean'
          })
    )

    return career_arsenal
