from flask import Flask, request, jsonify
import openai
from layers.layerone_modified import fetch_layer_one
from datetime import date
import os

openai.api_key = os.getenv("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")

app = Flask(__name__)
today = date.today().isoformat()
layer_one_data = fetch_layer_one(today)

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message")

    system_prompt = open("prompts/system_prompt.txt").read()
    system_prompt += f"\nData snapshot loaded for {today}. Respond using raw overlays when relevant."

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg}
        ]
    )

    reply = response["choices"][0]["message"]["content"]
    return jsonify({"response": reply})
