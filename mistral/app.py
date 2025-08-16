import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from mistralai.client import MistralClient
# This is the correct import for the new version
from mistralai.models.chat import ChatMessage

load_dotenv()
app = Flask(__name__)

# ... (the rest of the file is correct as previously provided) ...

# --- CONFIGURATIONS ---
MISTRAL_API_KEY = os.environ.get('MISTRAL_API_KEY')
if not MISTRAL_API_KEY:
    raise ValueError("MISTRAL_API_KEY not found in environment variables.")

client = MistralClient(api_key=MISTRAL_API_KEY)
MISTRAL_MODEL = "mistral-large-latest"

@app.route('/api/generate', methods=['POST'])
def generate():
    data = request.get_json()
    if not data or 'messages' not in data:
        return jsonify({'error': 'No messages provided'}), 400

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
    app.run(debug=True, host='0.0.0.0', port=5004)