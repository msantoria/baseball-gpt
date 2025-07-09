import requests
import pandas as pd
from datetime import datetime

# Odds API key and endpoint
ODDS_API_KEY = "033b32b81100ed7307e2376a6edd0353"
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"

# Supported markets
MARKETS = [
    "h2h",        # Moneyline
    "spreads",    # Runline
    "totals"      # Full-game Over/Under
]

def fetch_layer_twelve(game_date: str) -> pd.DataFrame:
    """
    Fetches MLB betting odds across all supported markets.
    """
    params = {
        "apiKey":     ODDS_API_KEY,
        "regions":    "us",
        "markets":    ",".join(MARKETS),
        "oddsFormat": "decimal"
    }

    resp = requests.get(ODDS_API_URL, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    records = []
    for game in data:
        game_pk = game.get("id")
        home_team = game.get("home_team")
        away_team = game.get("away_team")
        commence_time = game.get("commence_time")

        for bm in game.get("bookmakers", []):
            book = bm.get("title", "")
            last_update = bm.get("last_update", "")
            for market in bm.get("markets", []):
                mtype = market.get("key")
                for outcome in market.get("outcomes", []):
                    name = outcome.get("name")
                    price = outcome.get("price")
                    point = outcome.get("point", None)
                    implied = round((1 / price) * 100, 2) if price else None

                    records.append({
                        "GamePk":        game_pk,
                        "Bookmaker":     book,
                        "MarketType":    mtype,
                        "TeamOrPlayer":  name,
                        "Odds":          price,
                        "ImpliedProb":   implied,
                        "Line":          point,
                        "HomeTeam":      home_team,
                        "AwayTeam":      away_team,
                        "CommenceTime":  commence_time,
                        "LastUpdate":    last_update
                    })

    return pd.DataFrame(records)

if __name__ == '__main__':
    today = datetime.today().strftime('%Y-%m-%d')
    df = fetch_layer_twelve(today)
    df.to_csv(f'layer12_output_{today}.csv', index=False)
    print(f"✅ Output saved: layer12_output_{today}.csv")
