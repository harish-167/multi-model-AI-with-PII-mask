import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

app = Flask(__name__)

# --- CONFIGURATIONS ---
MISTRAL_API_KEY = os.environ.get('MISTRAL_API_KEY')
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"  # Update if the endpoint changes

if not MISTRAL_API_KEY:
    raise ValueError("MISTRAL_API_KEY not found in environment variables.")

@app.route('/api/generate', methods=['POST'])
def generate():
    data = request.get_json()
    if not data or 'messages' not in data:
        return jsonify({'error': 'No messages provided'}), 400

    messages_to_send = data['messages']

    try:
        headers = {
            "Authorization": f"Bearer {MISTRAL_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "mistral-tiny",  # Update with the model you want to use
            "messages": messages_to_send
        }

        response = requests.post(MISTRAL_API_URL, headers=headers, json=payload)
        response.raise_for_status()  # Raises an HTTPError for bad responses

        raw_mistral_response = response.json()
        # Extract the assistant's reply from the response
        # The exact structure depends on Mistral's API response format
        # This is a placeholder; adjust according to the actual response
        if 'choices' not in raw_mistral_response or not raw_mistral_response['choices']:
            return jsonify({'error': 'No response from Mistral API'}), 500

        # Assuming the response is in the format: {'choices': [{'message': {'content': '...'}}]}
        assistant_reply = raw_mistral_response['choices'][0]['message']['content']

        return jsonify({'response': assistant_reply})

    except requests.exceptions.RequestException as e:
        print(f"Error calling Mistral API: {e}")
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # The port is 5004 as per your original request
    app.run(debug=True, host='0.0.0.0', port=5004)

