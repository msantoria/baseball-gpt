# layer13_modified.py

import pandas as pd
from pybaseball import statcast, playerid_reverse_lookup
from datetime import datetime, timedelta


def fetch_layer_thirteen() -> pd.DataFrame:
    """
    Bill James Sabermetrics Layer (Layer 13 Extended)
    Pulls Statcast data for the last 30 days and calculates:
    - Runs Created (RC)
    - Secondary Average (SecA)
    - RC per 27 Outs (RC27)
    - Plus expanded Statcast metrics
    """
    end_date = datetime.today()
    start_date = end_date - timedelta(days=30)
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')

    df = statcast(start_str, end_str)
    if df.empty:
        return pd.DataFrame()

    df = df[df['events'].notna() & df['description'].notna()].copy()

    # Original hit types
    df['1B'] = (df['events'] == 'single').astype(int)
    df['2B'] = (df['events'] == 'double').astype(int)
    df['3B'] = (df['events'] == 'triple').astype(int)
    df['HR'] = (df['events'] == 'home_run').astype(int)
    df['BB'] = df['description'].str.contains('walk', na=False).astype(int)
    df['H'] = df[['1B', '2B', '3B', 'HR']].sum(axis=1)
    df['TB'] = df['1B'] + 2 * df['2B'] + 3 * df['3B'] + 4 * df['HR']

    # Approximate AB by excluding non-AB events
    non_ab_events = ['walk', 'hit_by_pitch', 'sac_fly', 'sac_bunt', 'intent_walk', 'catcher_interf']
    df['AB'] = (~df['events'].isin(non_ab_events)).astype(int)

    df['SB'] = (df['events'] == 'stolen_base').astype(int)
    df['CS'] = (df['events'] == 'caught_stealing').astype(int)
    df['K'] = df['events'].eq('strikeout').astype(int)

    df['OUTS'] = df['AB'] - df['H']

    # Clean statcast metrics
    df['launch_speed'] = pd.to_numeric(df['launch_speed'], errors='coerce')
    df['launch_angle'] = pd.to_numeric(df['launch_angle'], errors='coerce')
    df['estimated_woba_using_speedangle'] = pd.to_numeric(df['estimated_woba_using_speedangle'], errors='coerce')
    df['estimated_ba_using_speedangle'] = pd.to_numeric(df['estimated_ba_using_speedangle'], errors='coerce')

    # Group by batter
    summary = df.groupby('batter').agg({
        'H': 'sum',
        'BB': 'sum',
        'TB': 'sum',
        'AB': 'sum',
        'OUTS': 'sum',
        'SB': 'sum',
        'CS': 'sum',
        '1B': 'sum',
        '2B': 'sum',
        '3B': 'sum',
        'HR': 'sum',
        'K': 'sum',
        'launch_speed': 'mean',
        'launch_angle': 'mean',
        'estimated_woba_using_speedangle': 'mean',
        'estimated_ba_using_speedangle': 'mean'
    }).rename_axis('Batter ID').reset_index()

    # Rename new statcast columns
    summary.rename(columns={
        'launch_speed': 'AvgEV',
        'launch_angle': 'AvgLA',
        'estimated_woba_using_speedangle': 'xwOBA',
        'estimated_ba_using_speedangle': 'xBA'
    }, inplace=True)

    # Derived advanced sabermetric stats
    summary['RC'] = ((summary['H'] + summary['BB']) * summary['TB']) / (summary['AB'] + summary['BB'])
    summary['SecA'] = (summary['BB'] + (summary['TB'] - summary['H']) + (summary['SB'] - summary['CS'])) / summary['AB']
    summary['RC27'] = 27 * (summary['RC'] / summary['OUTS'])
    summary['K%'] = summary['K'] / summary['AB']
    summary['BABIP'] = (summary['H'] - summary['HR']) / (summary['AB'] - summary['K'] - summary['HR'])

    # Lookup player names
    ids = summary['Batter ID'].unique()
    lookup = playerid_reverse_lookup(ids, key_type="mlbam")
    lookup['Player Name'] = lookup['name_first'] + ' ' + lookup['name_last']
    lookup = lookup[['key_mlbam', 'Player Name']].rename(columns={'key_mlbam': 'Batter ID'})
    summary = summary.merge(lookup, on='Batter ID', how='left')

    # Output columns
    cols = [
        'Player Name', 'Batter ID', 'H', 'BB', 'TB', 'AB', 'OUTS',
        '1B', '2B', '3B', 'HR', 'SB', 'CS', 'K',
        'RC', 'SecA', 'RC27', 'K%', 'BABIP', 'xwOBA', 'xBA', 'AvgEV', 'AvgLA'
    ]
    return summary[cols]


if __name__ == "__main__":
    df = fetch_layer_thirteen()
    today = datetime.today().strftime('%Y-%m-%d')
    df.to_csv(f'layer13_output_{today}.csv', index=False)
    print(f"✅ Output saved: layer13_output_{today}.csv")
