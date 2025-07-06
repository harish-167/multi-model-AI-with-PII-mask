import os
import re
import spacy
from flask import Flask, request, jsonify

app = Flask(__name__)

# Load the spaCy model once when the application starts for efficiency
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading spaCy model 'en_core_web_sm'...")
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# Define regex patterns for common PII
# A simple regex for email addresses
EMAIL_REGEX = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
# A regex for common phone number formats
PHONE_REGEX = r'(\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b)'


@app.route('/api/mask-pii', methods=['POST'])
def mask_pii():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400

    original_text = data['text']
    masked_text = original_text
    mappings = {}
    
    # --- 1. Regex-based masking ---
    # Mask emails
    for i, match in enumerate(re.finditer(EMAIL_REGEX, masked_text)):
        placeholder = f"[EMAIL-{i+1}]"
        mappings[placeholder] = match.group(0)
        masked_text = masked_text.replace(match.group(0), placeholder, 1)

    # Mask phone numbers
    for i, match in enumerate(re.finditer(PHONE_REGEX, masked_text)):
        placeholder = f"[PHONE-{i+1}]"
        mappings[placeholder] = match.group(0)
        masked_text = masked_text.replace(match.group(0), placeholder, 1)
        
    # --- 2. SpaCy-based masking for Named Entities ---
    doc = nlp(masked_text)
    
    # We create a list of tokens to be replaced to avoid modifying the text while iterating
    replacements = []
    
    # We focus on names (PERSON), locations (GPE, LOC), and organizations (ORG)
    pii_labels = {"PERSON", "GPE", "LOC", "ORG"}
    
    for ent in doc.ents:
        if ent.label_ in pii_labels and not ent.text.startswith('['):
            placeholder = f"[{ent.label_}-{len(mappings) + 1}]"
            mappings[placeholder] = ent.text
            # Replace the entity text with the placeholder
            replacements.append((ent.text, placeholder))
            
    # Apply replacements from SpaCy
    for original, placeholder in replacements:
        masked_text = masked_text.replace(original, placeholder)

    return jsonify({
        'masked_text': masked_text,
        'mappings': mappings # Returning mappings is useful for potential de-masking
    })


if __name__ == '__main__':
    # The port is 5002 to avoid conflict with other services
    app.run(debug=True, host='0.0.0.0', port=5002)