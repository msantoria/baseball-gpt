import pandas as pd
from pybaseball import statcast
from datetime import datetime, timedelta

def fetch_layer_four(game_date: str) -> pd.DataFrame:
    end_dt = datetime.today()
    start_dt = end_dt - timedelta(days=365)  # faster pull
    start_str = start_dt.strftime('%Y-%m-%d')
    end_str = end_dt.strftime('%Y-%m-%d')

    print(f"⭭️ Pulling Statcast data from {start_str} to {end_str}…")

    raw = statcast(start_dt=start_str, end_dt=end_str)
    print(f"✅ Pulled {len(raw)} rows")

    raw['launch_speed'] = pd.to_numeric(raw['launch_speed'], errors='coerce')
    raw['launch_angle'] = pd.to_numeric(raw['launch_angle'], errors='coerce')
    raw['hit_distance_sc'] = pd.to_numeric(raw['hit_distance_sc'], errors='coerce')
    raw['Pitcher Name'] = raw['player_name']

    raw['barrel'] = (
        (raw['launch_speed'] >= 98) &
        raw['launch_angle'].between(26, 30)
    ).fillna(False).astype(int)
    raw['hard_hit'] = (raw['launch_speed'] >= 95).fillna(False).astype(int)

    # Safe list of fields to aggregate
    candidate_fields = {
        'release_speed': 'mean',
        'release_spin_rate': 'mean',
        'release_extension': 'mean',
        'release_pos_x': 'mean',
        'release_pos_z': 'mean',
        'pfx_x': 'mean',
        'pfx_z': 'mean',
        'break_length': 'mean',
        'break_angle': 'mean',
        'spin_axis': 'mean',
        'plate_x': 'mean',
        'plate_z': 'mean',
        'vx0': 'mean',
        'vy0': 'mean',
        'vz0': 'mean',
        'ax': 'mean',
        'ay': 'mean',
        'az': 'mean',
        'hit_distance_sc': 'mean',
        'launch_speed': 'mean',
        'launch_angle': 'mean',
        'estimated_woba_using_speedangle': 'mean',
        'estimated_ba_using_speedangle': 'mean',
        'zone': 'mean',
        'outs_when_up': 'mean',
        'inning': 'mean',
        'barrel': 'sum',
        'hard_hit': 'sum',
        'events': 'count'
    }

    # Only use fields that are actually present
    agg_fields = {k: v for k, v in candidate_fields.items() if k in raw.columns}

    stats = raw.groupby(['pitcher', 'Pitcher Name'], as_index=False).agg(agg_fields)

    stats['HardHit%'] = (stats['hard_hit'] / stats['events']) * 100
    stats['Barrel%'] = (stats['barrel'] / stats['events']) * 100

    stats.rename(columns={
        'pitcher': 'Pitcher ID',
        'release_speed': 'Avg Velo',
        'release_spin_rate': 'Avg Spin Rate',
        'release_extension': 'Avg Extension',
        'release_pos_x': 'Rel Pos X',
        'release_pos_z': 'Rel Pos Z',
        'pfx_x': 'Horz Break',
        'pfx_z': 'Vert Break',
        'break_length': 'Break Length',
        'break_angle': 'Break Angle',
        'spin_axis': 'Spin Axis',
        'plate_x': 'Plate X',
        'plate_z': 'Plate Z',
        'vx0': 'vx0', 'vy0': 'vy0', 'vz0': 'vz0',
        'ax': 'ax', 'ay': 'ay', 'az': 'az',
        'hit_distance_sc': 'Avg Hit Distance',
        'launch_speed': 'Avg Exit Velo',
        'launch_angle': 'Avg Launch Angle',
        'estimated_woba_using_speedangle': 'xwOBA',
        'estimated_ba_using_speedangle': 'xBA',
        'zone': 'Avg Zone',
        'outs_when_up': 'Avg Outs',
        'inning': 'Avg Inning'
    }, inplace=True)

    # Build final column list safely
    always_keep = ['Pitcher ID', 'Pitcher Name', 'events', 'HardHit%', 'Barrel%']
    maybe_fields = [
        'Avg Velo', 'Avg Spin Rate', 'xwOBA', 'xBA',
        'Avg Extension', 'Rel Pos X', 'Rel Pos Z',
        'Horz Break', 'Vert Break', 'Break Length', 'Break Angle',
        'Spin Axis', 'Plate X', 'Plate Z',
        'vx0', 'vy0', 'vz0', 'ax', 'ay', 'az',
        'Avg Hit Distance', 'Avg Exit Velo', 'Avg Launch Angle',
        'Avg Zone', 'Avg Outs', 'Avg Inning'
    ]
    final_cols = always_keep + [col for col in maybe_fields if col in stats.columns]

    return stats[final_cols]

if __name__ == "__main__":
    today = datetime.today().date().isoformat()
    df = fetch_layer_four(today)
    df.to_csv(f"layerfour_output_{today}.csv", index=False)
    print(f"✅ Output saved to layerfour_output_{today}.csv")
