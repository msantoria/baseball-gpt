# layerseven_modified.py

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pybaseball import statcast
from tqdm import tqdm

def fetch_layer_seven(end_date: str) -> pd.DataFrame:
    print("📦 Pulling full Statcast dataset...")
    start_dt = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=365)).strftime('%Y-%m-%d')
    df = statcast(start_dt, end_date)

    if df.empty:
        print("❌ No Statcast data found.")
        return pd.DataFrame()

    print("🔍 Filtering out starting pitchers...")

    # Detect starters: pitchers who pitched in inning 1 with 0 outs
    df['is_starter'] = (df['inning'] == 1) & (df['outs_when_up'] == 0)
    starters = df[df['is_starter']]['pitcher'].unique()
    df_relievers = df[~df['pitcher'].isin(starters)].copy()

    if df_relievers.empty:
        print("❌ No reliever data after filtering.")
        return pd.DataFrame()

    print("📊 Aggregating reliever data by team...")

    # Clean relevant numeric fields
    numeric_fields = [
        'release_speed', 'release_extension', 'spin_rate_deprecated',
        'launch_speed', 'launch_angle',
        'estimated_woba_using_speedangle', 'estimated_ba_using_speedangle'
    ]
    for col in numeric_fields:
        df_relievers[col] = pd.to_numeric(df_relievers[col], errors='coerce')

    # Create swing & miss indicators
    df_relievers['is_swing'] = df_relievers['description'].isin([
        'swinging_strike', 'foul', 'foul_tip',
        'hit_into_play', 'hit_into_play_score', 'hit_into_play_no_out'
    ])
    df_relievers['is_whiff'] = df_relievers['description'].isin([
        'swinging_strike', 'swinging_strike_blocked'
    ])
    df_relievers['is_k'] = df_relievers['events'] == 'strikeout'
    df_relievers['is_bb'] = df_relievers['events'] == 'walk'
    df_relievers['is_hr'] = df_relievers['events'] == 'home_run'
    df_relievers['hard_hit'] = pd.to_numeric(df_relievers['launch_speed'], errors='coerce') >= 95

    # Group by team (from home_team field)
    grouped = df_relievers.groupby('home_team')

    records = []
    for team, group in grouped:
        swings = group['is_swing'].sum()
        whiffs = group['is_whiff'].sum()
        PA = len(group)
        ks = group['is_k'].sum()
        bbs = group['is_bb'].sum()
        hrs = group['is_hr'].sum()
        hards = group['hard_hit'].sum()

        record = {
            'Team': team,
            'PA': PA,
            'Whiff%': whiffs / swings if swings > 0 else np.nan,
            'K%': ks / PA,
            'BB%': bbs / PA,
            'HR/9': (hrs / (PA / 3)) * 9,
            'HardHit%': hards / PA,
            'Avg EV': group['launch_speed'].mean(),
            'Avg LA': group['launch_angle'].mean(),
            'xwOBA': group['estimated_woba_using_speedangle'].mean(),
            'xBA': group['estimated_ba_using_speedangle'].mean(),
            'Release Velo': group['release_speed'].mean(),
            'Release Extension': group['release_extension'].mean(),
            'Spin Rate': group['spin_rate_deprecated'].mean()
        }
        records.append(record)

    return pd.DataFrame(records)

# Main execution
if __name__ == '__main__':
    today = datetime.today().strftime('%Y-%m-%d')
    df = fetch_layer_seven(today)
    if not df.empty:
        output_file = f'layerseven_output_{today}.csv'
        df.to_csv(output_file, index=False)
        print(f"✅ Output saved: {output_file}")
    else:
        print("⚠️ No data to write.")
