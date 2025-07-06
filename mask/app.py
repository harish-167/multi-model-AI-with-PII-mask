import os
import re
import spacy
from flask import Flask, request, jsonify

app = Flask(__name__)

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading spaCy model 'en_core_web_sm'...")
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

EMAIL_REGEX = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
PHONE_REGEX = r'(\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b)'

@app.route('/api/mask-pii', methods=['POST'])
def mask_pii():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400

    text_to_mask = data['text']
    
    # --- START OF NEW LOGIC ---
    # 1. Create a map to store PII and its corresponding unique placeholder for this request.
    pii_map = {}
    
    # Use a list to store replacements to handle them in a controlled way later.
    replacements = []

    # --- Pass 1: Find all PII entities and create consistent mappings ---

    # Find entities with spaCy first
    doc = nlp(text_to_mask)
    pii_labels = {"PERSON", "GPE", "LOC", "ORG"}
    for ent in doc.ents:
        if ent.label_ in pii_labels:
            if ent.text not in pii_map:
                # Create a new placeholder if this entity is seen for the first time
                placeholder = f"[{ent.label_}-{len(pii_map) + 1}]"
                pii_map[ent.text] = placeholder
            # Add to our list of replacements
            replacements.append((ent.text, pii_map[ent.text]))

    # Find entities with regex
    for match in re.finditer(EMAIL_REGEX, text_to_mask):
        if match.group(0) not in pii_map:
            placeholder = f"[EMAIL-{len(pii_map) + 1}]"
            pii_map[match.group(0)] = placeholder
        replacements.append((match.group(0), pii_map[match.group(0)]))
        
    for match in re.finditer(PHONE_REGEX, text_to_mask):
        if match.group(0) not in pii_map:
            placeholder = f"[PHONE-{len(pii_map) + 1}]"
            pii_map[match.group(0)] = placeholder
        replacements.append((match.group(0), pii_map[match.group(0)]))

    # --- Pass 2: Apply all replacements ---
    
    # Sort replacements by length of the original string (descending)
    # This prevents issues where a shorter name is part of a longer name (e.g., "Bob" in "Bob Smith")
    sorted_replacements = sorted(list(set(replacements)), key=lambda item: len(item[0]), reverse=True)

    masked_text = text_to_mask
    for original_pii, placeholder in sorted_replacements:
        masked_text = masked_text.replace(original_pii, placeholder)
    
    # --- END OF NEW LOGIC ---

    return jsonify({'masked_text': masked_text})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)