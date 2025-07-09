# layereight_modified.py

import pandas as pd
import requests
from datetime import datetime

def fetch_layer_eight(date_str: str) -> pd.DataFrame:
    """
    Pulls all available game-level metadata for each scheduled MLB game on the date,
    including venue, weather, wind speed/direction, game type, and series context.
    """
    url = (
        f"https://statsapi.mlb.com/api/v1/schedule"
        f"?sportId=1&date={date_str}&hydrate=venue,weather"
    )

    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    records = []
    for date_block in data.get("dates", []):
        for game in date_block.get("games", []):
            venue = game.get("venue", {})
            weather = game.get("weather", {})

            records.append({
                "GamePk":                 game.get("gamePk"),
                "Official Date":         game.get("officialDate"),
                "Game Time (UTC)":       game.get("gameDate"),
                "Game Type":             game.get("gameType"),
                "Series Description":    game.get("seriesDescription"),
                "Series Game Number":    game.get("seriesGameNumber"),
                "Doubleheader":          game.get("doubleHeader"),
                "Venue":                 venue.get("name"),
                "Venue ID":              venue.get("id"),
                "Home Team":             game["teams"]["home"]["team"]["name"],
                "Away Team":             game["teams"]["away"]["team"]["name"],
                "Condition":             weather.get("condition"),
                "Temp (F)":              weather.get("temp"),
                "Wind (text)":           weather.get("wind"),
                "Wind Speed (mph)":      weather.get("windSpeed"),
                "Wind Direction":        weather.get("windDirection")
            })

    return pd.DataFrame(records)

if __name__ == "__main__":
    today = datetime.today().strftime("%Y-%m-%d")
    df = fetch_layer_eight(today)
    df.to_csv(f"layereight_output_{today}.csv", index=False)
    print(f"✅ Output saved: layereight_output_{today}.csv")
