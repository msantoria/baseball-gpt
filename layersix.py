# layersix_modified.py

import pandas as pd
import requests
import os
from pybaseball import statcast_batter, statcast_pitcher
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from pandas.errors import ParserError

def fetch_layer_six(date_str: str) -> pd.DataFrame:
    today = date_str
    start_dt = (datetime.strptime(date_str, "%Y-%m-%d") - timedelta(days=365)).strftime("%Y-%m-%d")

    # 1) Pull today's schedule and probable pitchers
    sched = requests.get(
        f"https://statsapi.mlb.com/api/v1/schedule?"
        f"sportId=1&date={today}&hydrate=probablePitcher"
    ).json()

    hitters = []
    for date_block in sched.get('dates', []):
        for game in date_block.get('games', []):
            game_time = game['gameDate']
            home = game['teams']['home']
            away = game['teams']['away']
            home_pid = home.get('probablePitcher', {}).get('id')
            away_pid = away.get('probablePitcher', {}).get('id')

            box = requests.get(
                f"https://statsapi.mlb.com/api/v1/game/{game['gamePk']}/boxscore"
            ).json()

            for side, pid, team in [
                ('home', away_pid, away['team']['name']),
                ('away', home_pid, home['team']['name'])
            ]:
                if not pid:
                    continue
                for p in box['teams'][side]['players'].values():
                    if 'batting' in p.get('stats', {}):
                        hitters.append({
                            'Game Time':          game_time,
                            'Team':               team,
                            'Batter':             p['person']['fullName'],
                            'Batter ID':          p['person']['id'],
                            'Opposing Pitcher ID': pid
                        })

    df_hitters = pd.DataFrame(hitters).dropna(subset=['Batter ID', 'Opposing Pitcher ID'])
    if df_hitters.empty:
        return pd.DataFrame()

    # 2) Build each pitcher's top-3 pitch mix
    pitcher_map = {}
    for pid in df_hitters['Opposing Pitcher ID'].unique():
        try:
            pdf = statcast_pitcher(start_dt, today, int(pid))
            mix = pdf['pitch_type'].value_counts(normalize=True)
            pitcher_map[pid] = mix[mix > 0.05].nlargest(3).index.tolist()
        except Exception:
            pitcher_map[pid] = []

    os.makedirs("overlay_cache", exist_ok=True)

    # 3) Overlay: Batter vs Pitch Type performance table
    def overlay_batter(bid):
        cache_path = f"overlay_cache/batter_{bid}.csv"
        if os.path.exists(cache_path):
            try:
                return pd.read_csv(cache_path)
            except Exception:
                pass  # fallback to re-pull if read fails

        try:
            bdf = statcast_batter(start_dt, today, int(bid))
            if bdf.empty:
                return pd.DataFrame()

            bdf['is_swing'] = bdf['description'].isin([
                'swinging_strike', 'foul', 'foul_tip',
                'hit_into_play', 'hit_into_play_score', 'hit_into_play_no_out'
            ])
            bdf['is_whiff'] = bdf['description'].isin(['swinging_strike', 'swinging_strike_blocked'])
            bdf['is_k'] = bdf['events'] == 'strikeout'
            bdf['is_putaway'] = (bdf['strikes'] == 2) & (bdf['description'] == 'swinging_strike')
            bdf['is_two_strike'] = bdf['strikes'] == 2
            bdf['hard_hit'] = pd.to_numeric(bdf['launch_speed'], errors='coerce') >= 95

            for col in [
                'launch_speed', 'launch_angle', 'estimated_woba_using_speedangle', 'estimated_ba_using_speedangle',
                'release_speed', 'release_pos_x', 'release_pos_z',
                'pfx_x', 'pfx_z', 'plate_x', 'plate_z', 'sz_top', 'sz_bot'
            ]:
                bdf[col] = pd.to_numeric(bdf[col], errors='coerce')

            bdf = bdf[bdf['pitch_type'].notnull()]  # remove rows without pitch_type

            g = bdf.groupby('pitch_type', as_index=False).agg({
                'pitch_type': 'first',  # retain for merge later
                'is_swing': 'sum',
                'is_whiff': 'sum',
                'is_k': 'sum',
                'is_putaway': 'sum',
                'is_two_strike': 'sum',
                'estimated_woba_using_speedangle': 'mean',
                'estimated_ba_using_speedangle': 'mean',
                'launch_speed': 'mean',
                'launch_angle': 'mean',
                'hard_hit': 'sum',
                'release_speed': 'mean',
                'release_pos_x': 'mean',
                'release_pos_z': 'mean',
                'pfx_x': 'mean',
                'pfx_z': 'mean',
                'plate_x': 'mean',
                'plate_z': 'mean',
                'sz_top': 'mean',
                'sz_bot': 'mean'
            }).rename(columns={
                'is_swing': 'Swings',
                'is_whiff': 'Whiffs',
                'is_k': 'Strikeouts',
                'is_putaway': 'PutAwaySwings',
                'is_two_strike': 'TwoStrikePitches',
                'estimated_woba_using_speedangle': 'xwOBA',
                'estimated_ba_using_speedangle': 'xBA',
                'launch_speed': 'Avg EV',
                'launch_angle': 'Avg LA',
                'hard_hit': 'HardHits'
            })

            g['PA'] = g['Swings'] + (g['Strikeouts'] - g['Whiffs'])
            g['Whiff%'] = g['Whiffs'] / g['Swings']
            g['K%'] = g['Strikeouts'] / g['PA']
            g['PutAway%'] = g['PutAwaySwings'] / g['TwoStrikePitches']
            g['HardHit%'] = g['HardHits'] / g['PA']

            g['Batter ID'] = bid
            g.to_csv(cache_path, index=False)
            return g
        except ParserError:
            return pd.DataFrame()

    records = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(overlay_batter, bid): bid for bid in df_hitters['Batter ID'].unique()}
        for future in as_completed(futures):
            result = future.result()
            if not result.empty:
                records.append(result)

    if not records:
        return pd.DataFrame()

    df_overlay = pd.concat(records, ignore_index=True)
    df_merged = df_hitters.merge(df_overlay, how='left', on='Batter ID')

    df_merged = df_merged[df_merged['pitch_type'].isin(
        df_merged['Opposing Pitcher ID'].map(pitcher_map).explode().dropna()
    )]

    return df_merged

if __name__ == '__main__':
    today = datetime.today().strftime('%Y-%m-%d')
    df = fetch_layer_six(today)
    df.to_csv(f'layersix_output_{today}.csv', index=False)
    print(f"✅ Output saved: layersix_output_{today}.csv")
