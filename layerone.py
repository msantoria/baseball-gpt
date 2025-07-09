import pandas as pd
import requests
from pybaseball import statcast_pitcher
from datetime import date, timedelta

def fetch_layer_one(game_date: str) -> pd.DataFrame:
    schedule_url = (
        f"https://statsapi.mlb.com/api/v1/schedule"
        f"?sportId=1&date={game_date}&hydrate=probablePitcher(note)"
    )
    res = requests.get(schedule_url)
    res.raise_for_status()
    schedule_data = res.json()

    games = []
    pitcher_ids = set()

    for day in schedule_data.get('dates', []):
        for game in day.get('games', []):
            home = game['teams']['home']
            away = game['teams']['away']

            rec = {
                'Game Time (UTC)': game['gameDate'],
                'Away Team': away['team']['name'],
                'Home Team': home['team']['name'],
            }

            for side, prefix in [(away, 'Away'), (home, 'Home')]:
                pp = side.get('probablePitcher', {})
                pid = pp.get('id')
                name = pp.get('fullName', 'TBD')
                rec[f'{prefix} Pitcher'] = name
                rec[f'{prefix} Pitcher ID'] = pid
                if pid is not None:
                    pitcher_ids.add(pid)

            games.append(rec)

    games_df = pd.DataFrame(games).dropna(
        subset=['Away Pitcher ID', 'Home Pitcher ID']
    )

    # Step 2: Pull Statcast for each pitcher for last 365 days
    start_date = (pd.to_datetime(game_date) - timedelta(days=365)).strftime('%Y-%m-%d')
    statcast_dfs = []

    for pid in pitcher_ids:
        print(f"📦 Pulling Statcast for pitcher ID: {pid}...")
        try:
            df = statcast_pitcher(start_date, game_date, pid)
            if not df.empty:
                df['pitcher_id'] = pid
                statcast_dfs.append(df)
        except Exception as e:
            print(f"❌ Failed for pitcher {pid}: {e}")
            continue

    if not statcast_dfs:
        print("⚠️ No data fetched.")
        return games_df

    pitcher_data = pd.concat(statcast_dfs, ignore_index=True)

    # Step 3: Aggregate traits and new metrics
    agg = (
        pitcher_data
        .assign(
            is_K=lambda d: d['events'] == 'strikeout',
            is_BB=lambda d: d['events'] == 'walk'
        )
        .groupby('pitcher_id')
        .agg(
            Velo=('release_speed', 'mean'),
            Spin=('release_spin_rate', 'mean'),
            HardHit=('launch_speed', 'mean'),
            K_cnt=('is_K', 'sum'),
            BB_cnt=('is_BB', 'sum'),
            Pitches=('events', 'count'),
            xwOBA=('estimated_woba_using_speedangle', 'mean'),
            xBA=('estimated_ba_using_speedangle', 'mean'),
            VertBreak=('pfx_z', 'mean'),
            HorzBreak=('pfx_x', 'mean'),
            ReleaseExtension=('release_extension', 'mean'),
            ReleasePosX=('release_pos_x', 'mean'),
            ReleasePosZ=('release_pos_z', 'mean')
        )
        .assign(
            **{
                'K %': lambda df: 100 * df['K_cnt'] / df['Pitches'],
                'BB %': lambda df: 100 * df['BB_cnt'] / df['Pitches']
            }
        )
        .reset_index()[[
            'pitcher_id', 'Velo', 'Spin', 'HardHit', 'K %', 'BB %',
            'xwOBA', 'xBA', 'VertBreak', 'HorzBreak',
            'ReleaseExtension', 'ReleasePosX', 'ReleasePosZ'
        ]]
    )

    # Step 4: Merge enriched data into game-level frame
    out = (
        games_df
        .merge(agg, how='left', left_on='Away Pitcher ID', right_on='pitcher_id')
        .rename(columns={
            'Velo': 'Away Velo', 'Spin': 'Away Spin', 'HardHit': 'Away Hard Hit %',
            'K %': 'Away K %', 'BB %': 'Away BB %', 'xwOBA': 'Away xwOBA', 'xBA': 'Away xBA',
            'VertBreak': 'Away Vert Break', 'HorzBreak': 'Away Horz Break',
            'ReleaseExtension': 'Away Release Extension',
            'ReleasePosX': 'Away Rel Pos X', 'ReleasePosZ': 'Away Rel Pos Z'
        })
        .drop(columns=['pitcher_id'])
        .merge(agg, how='left', left_on='Home Pitcher ID', right_on='pitcher_id')
        .rename(columns={
            'Velo': 'Home Velo', 'Spin': 'Home Spin', 'HardHit': 'Home Hard Hit %',
            'K %': 'Home K %', 'BB %': 'Home BB %', 'xwOBA': 'Home xwOBA', 'xBA': 'Home xBA',
            'VertBreak': 'Home Vert Break', 'HorzBreak': 'Home Horz Break',
            'ReleaseExtension': 'Home Release Extension',
            'ReleasePosX': 'Home Rel Pos X', 'ReleasePosZ': 'Home Rel Pos Z'
        })
        .drop(columns=['pitcher_id'])
    )

    return out

# Entry point
if __name__ == "__main__":
    today = date.today().isoformat()
    df = fetch_layer_one(today)
    df.to_csv(f"layerone_output_{today}.csv", index=False)
    print(f"✅ Output saved to layerone_output_{today}.csv")
