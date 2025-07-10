from flask import Flask, request, jsonify
import openai
import os
from datetime import date
from layers.layerone_modified import fetch_layer_one

# Load OpenAI API key from environment
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("❌ Missing OPENAI_API_KEY environment variable.")

# Create app
app = Flask(__name__)

# Load today’s data once on startup
today = date.today().isoformat()
try:
    layer_one_data = fetch_layer_one(today)
    print(f"✅ Layer One data loaded for {today}, rows: {len(layer_one_data)}")
except Exception as e:
    print(f"⚠️ Failed to load Layer One: {e}")
    layer_one_data = None

# Ping route to test uptime
@app.route("/ping")
def ping():
    return "pong", 200

# Main chat endpoint
@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message", "")

    # Load system prompt
    try:
        with open("prompts/system_prompt.txt", "r") as f:
            system_prompt = f.read()
    except Exception:
        system_prompt = "You are Free Agent Analytics. Respond with overlays using loaded data."

    system_prompt += f"\nData snapshot loaded for {today}. Use `layer_one_data` if needed."

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg}
        ]
    )

    reply = response["choices"][0]["message"]["content"]
    return jsonify({"response": reply})


# Run server (Render needs this to bind to $PORT)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
