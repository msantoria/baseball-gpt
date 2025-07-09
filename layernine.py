import pandas as pd
import requests
import gspread
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from gspread_dataframe import set_with_dataframe
from oauth2client.service_account import ServiceAccountCredentials
import time

# --- SETTINGS ---
GOOGLE_JSON_PATH = r"C:\Users\micha\OneDrive\Documents\original-list-228219-394e2de44c62.json"
GOOGLE_SHEET_NAME = "MLB DM 5125"
SHEET_TAB = "LayerNine"
EMAIL = "michaelsantoria@gmail.com"
APP_PASSWORD = "NewPassword01$"  # REPLACE with Gmail App Password
SMS_GATEWAY = "6308008441@tmomail.net"  # Verizon

# --- AUTH ONCE ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_JSON_PATH, scope)
client = gspread.authorize(creds)
spreadsheet = client.open(GOOGLE_SHEET_NAME)

try:
    worksheet = spreadsheet.worksheet(SHEET_TAB)
except gspread.exceptions.WorksheetNotFound:
    worksheet = spreadsheet.add_worksheet(title=SHEET_TAB, rows="100", cols="20")

def send_sms_alert(message):
    msg = MIMEText(message)
    msg["From"] = EMAIL
    msg["To"] = SMS_GATEWAY
    msg["Subject"] = "Big Inning Alert 🚨"

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL, APP_PASSWORD)
            server.sendmail(EMAIL, SMS_GATEWAY, msg.as_string())
        print("📲 Text alert sent.")
    except Exception as e:
        print(f"❌ SMS send failed: {e}")

def detect_big_inning(row):
    try:
        return "🚨 Big Inning Threat" if int(row["Outs"]) <= 1 and int(row["Runners On"]) >= 2 else ""
    except:
        return ""

# --- MAIN LOOP FUNCTION ---
def run_layernine_sync():
    today = datetime.now().strftime('%Y-%m-%d')
    schedule_url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}"
    games = []

    try:
        schedule_data = requests.get(schedule_url).json()
        for date in schedule_data["dates"]:
            for game in date["games"]:
                gamePk = game["gamePk"]
                away = game["teams"]["away"]["team"]["name"]
                home = game["teams"]["home"]["team"]["name"]
                status = game["status"]["detailedState"]

                # Only include active or completed games
                if status not in ["Final", "Game Over", "Postponed"]:
                    try:
                        live_url = f"https://statsapi.mlb.com/api/v1.1/game/{gamePk}/feed/live"
                        live_data = requests.get(live_url).json()
                        plays = live_data.get("liveData", {}).get("plays", {})
                        linescore = live_data.get("liveData", {}).get("linescore", {})

                        inning = linescore.get("currentInning", "—")
                        half = linescore.get("inningHalf", "—")
                        current_play = plays.get("currentPlay", {})
                        outs = current_play.get("count", {}).get("outs", "—")
                        runners = len(current_play.get("runners", []))

                        away_team = linescore.get("teams", {}).get("away", {})
                        home_team = linescore.get("teams", {}).get("home", {})

                        games.append({
                            "Away": away,
                            "Home": home,
                            "Status": status,
                            "Inning": f"{half} {inning}",
                            "Outs": outs,
                            "Runners On": runners,
                            "Away Score": away_team.get("runs", "—"),
                            "Home Score": home_team.get("runs", "—"),
                            "Away Hits": away_team.get("hits", "—"),
                            "Home Hits": home_team.get("hits", "—"),
                            "Away Errors": away_team.get("errors", "—"),
                            "Home Errors": home_team.get("errors", "—")
                        })
                    except Exception:
                        games.append({
                            "Away": away, "Home": home, "Status": status,
                            "Inning": "N/A", "Outs": "N/A", "Runners On": "N/A",
                            "Away Score": "N/A", "Home Score": "N/A",
                            "Away Hits": "N/A", "Home Hits": "N/A",
                            "Away Errors": "N/A", "Home Errors": "N/A"
                        })

    except Exception as e:
        print(f"❌ Failed to fetch schedule: {e}")
        return False  # signal failure

    if not games:
        print("✅ All games finished.")
        return False  # signal to exit

    # Format and push
    df = pd.DataFrame(games)
    df["Big Inning"] = df.apply(detect_big_inning, axis=1)

    worksheet.clear()
    set_with_dataframe(worksheet, df)
    print(f"✅ Synced {len(df)} games to Google Sheet.")

    # Send SMS alert if needed
    alerts = df[df["Big Inning"] != ""]
    if not alerts.empty:
        alert_text = "\n".join(f"{row['Away']} @ {row['Home']} — {row['Inning']}" for _, row in alerts.iterrows())
        send_sms_alert(f"Big Inning(s):\n{alert_text}")

    return True  # keep going

# --- LOOP UNTIL ALL GAMES FINISH ---
if __name__ == "__main__":
    while True:
        keep_going = run_layernine_sync()
        if not keep_going:
            break
        print("⏳ Waiting 3 minutes before next update...\n")
        time.sleep(180)
