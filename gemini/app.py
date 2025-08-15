import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

app = Flask(__name__)

# --- CONFIGURATIONS ---
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables.")

# --- GOOGLE GENERATIVE AI CONFIGURATION ---
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')


@app.route('/api/generate', methods=['POST'])
def generate():
    data = request.get_json()
    if not data or 'messages' not in data:
        return jsonify({'error': 'No messages provided'}), 400

    messages_to_send = data['messages']

    try:
        # Use the stateless generate_content method
        response = model.generate_content(messages_to_send)
        
        if not response.parts:
            raw_gemini_response = "I am unable to respond to that prompt due to safety concerns."
        else:
            raw_gemini_response = response.text

        return jsonify({'response': raw_gemini_response})

    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # The port is 5003 to avoid conflict
    app.run(debug=True, host='0.0.0.0', port=5003)
