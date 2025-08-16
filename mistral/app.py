from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"  # Replace with the actual endpoint if different

@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.json
        if not data or "message" not in data:
            return jsonify({"error": "No message provided"}), 400

        user_message = data["message"]

        headers = {
            "Authorization": f"Bearer {MISTRAL_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "mistral-tiny",  # Replace with the model you want to use
            "messages": [{"role": "user", "content": user_message}]
        }

        response = requests.post(MISTRAL_API_URL, headers=headers, json=payload)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX, 5XX)

        return jsonify(response.json())

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to call Mistral API: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004)
