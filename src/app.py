import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure the Gemini API
try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-pro')
    # For simplicity, we create one chat session that persists as long as the app is running.
    # In a real multi-user app, you would manage chat histories per user session.
    chat = model.start_chat(history=[])
    print("Gemini model initialized successfully.")
except Exception as e:
    print(f"Error initializing Gemini: {e}")
    model = None
    chat = None

def application(environ, start_response):
    """
    The main WSGI application function.
    `environ` is a dictionary containing CGI-style environment variables.
    `start_response` is a function for sending the HTTP status and headers.
    """
    # --- Handle the chat request ---
    if environ['REQUEST_METHOD'] == 'POST' and environ['PATH_INFO'] == '/chat':
        if not chat:
            # Handle case where Gemini failed to initialize
            status = '500 Internal Server Error'
            headers = [('Content-type', 'application/json')]
            start_response(status, headers)
            error_response = {'response': 'Error: AI model is not configured.'}
            return [json.dumps(error_response).encode('utf-8')]

        try:
            # Get the length of the request body
            request_body_size = int(environ.get('CONTENT_LENGTH', 0))
        except (ValueError):
            request_body_size = 0

        # Read the user's message from the request body
        request_body = environ['wsgi.input'].read(request_body_size)
        data = json.loads(request_body)
        user_message = data.get('message', '')

        if not user_message:
            status = '400 Bad Request'
            headers = [('Content-type', 'application/json')]
            start_response(status, headers)
            error_response = {'response': 'Error: No message provided.'}
            return [json.dumps(error_response).encode('utf-8')]

        # Send message to Gemini and get the response
        try:
            response = chat.send_message(user_message, stream=True)
            ai_response_content = "".join([chunk.text for chunk in response])
        except Exception as e:
            status = '500 Internal Server Error'
            headers = [('Content-type', 'application/json')]
            start_response(status, headers)
            error_response = {'response': f'Error from AI API: {e}'}
            return [json.dumps(error_response).encode('utf-8')]


        # Send a successful response back to the client
        status = '200 OK'
        headers = [('Content-type', 'application/json')]
        start_response(status, headers)
        
        response_data = {'response': ai_response_content}
        return [json.dumps(response_data).encode('utf-8')]

    # --- Handle all other requests with a 404 ---
    else:
        status = '404 Not Found'
        headers = [('Content-type', 'text/plain')]
        start_response(status, headers)
        return [b'Not Found']