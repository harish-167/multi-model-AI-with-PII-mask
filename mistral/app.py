import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

# Load environment variables
load_dotenv()

app = Flask(__name__)

# --- CONFIGURATIONS ---
MISTRAL_API_KEY = os.environ.get('MISTRAL_API_KEY')
if not MISTRAL_API_KEY:
    raise ValueError("MISTRAL_API_KEY not found in environment variables.")

# --- MISTRAL AI CONFIGURATION ---
client = MistralClient(api_key=MISTRAL_API_KEY)
# We can specify the model to use here
MISTRAL_MODEL = "mistral-large-latest"


@app.route('/api/generate', methods=['POST'])
def generate():
    data = request.get_json()
    if not data or 'messages' not in data:
        return jsonify({'error': 'No messages provided'}), 400

    # Mistral's client expects a list of ChatMessage objects
    # The app-service will be responsible for formatting this correctly.
    try:
        messages_to_send = [
            ChatMessage(role=msg['role'], content=msg['content'])
            for msg in data['messages']
        ]

        chat_response = client.chat(
            model=MISTRAL_MODEL,
            messages=messages_to_send,
        )

        raw_mistral_response = chat_response.choices[0].message.content
        return jsonify({'response': raw_mistral_response})

    except Exception as e:
        print(f"Error calling Mistral API: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # The port is 5004 to avoid conflict
    app.run(debug=True, host='0.0.0.0', port=5004)