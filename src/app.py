import os
import google.generativeai as genai
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Configure Google Generative AI
# IMPORTANT: Replace "YOUR_GEMINI_API_KEY" with your actual API key
# It's highly recommended to use environment variables for production
# For this example, we'll put it directly, but for real apps, use:
# os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))

# Choose a model
model = genai.GenerativeModel('gemini-2.0-flash')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_text', methods=['POST'])
def generate_text():
    data = request.json
    user_prompt = data.get('prompt')
    # Receive the entire conversation history from the frontend
    conversation_history = data.get('history', [])
    if not user_prompt:
        return jsonify({'error': 'No prompt provided'}), 400

    try:
        chat = model.start_chat(history=conversation_history)
        # Send the new user message to the chat
        response = chat.send_message(user_prompt)

        #response = model.generate_content(user_prompt)
        # Assuming the response has a 'text' attribute
        generated_content = response.text
        
        # Update the conversation history with the new user input and model response
        # The chat.history object now contains the updated conversation.
        # We need to convert it to a serializable format for JSON.
        updated_history = [
            {'role': message.role, 'parts': [part.text for part in message.parts]}
            for message in chat.history
        ]

        return jsonify({
            'generated_text': generated_content,
            'history': updated_history # Send back the full updated history
        })
    except Exception as e:
        # Log the full exception for debugging
        print(f"Error calling Gemini API: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=5000) # debug=True allows for automatic reloads on code changes
