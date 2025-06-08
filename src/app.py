import os
import google.generativeai as genai
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Configure Google Generative AI
# IMPORTANT: Replace "YOUR_GEMINI_API_KEY" with your actual API key
# It's highly recommended to use environment variables for production
# For this example, we'll put it directly, but for real apps, use:
# os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key="YOUR-API-KEY")

# Choose a model
model = genai.GenerativeModel('gemini-2.0-flash')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_text', methods=['POST'])
def generate_text():
    user_prompt = request.json.get('prompt')
    if not user_prompt:
        return jsonify({'error': 'No prompt provided'}), 400

    try:
        response = model.generate_content(user_prompt)
        # Assuming the response has a 'text' attribute
        generated_content = response.text
        return jsonify({'generated_text': generated_content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=5000) # debug=True allows for automatic reloads on code changes
