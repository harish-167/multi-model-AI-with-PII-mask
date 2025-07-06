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

    original_text = data['text']
    masked_text = original_text
    
    # Use a set to keep track of unique PII entities found to avoid re-masking
    found_pii = set()

    # Regex-based masking
    for match in re.finditer(EMAIL_REGEX, masked_text):
        if match.group(0) not in found_pii:
            masked_text = masked_text.replace(match.group(0), "[EMAIL]", 1)
            found_pii.add(match.group(0))

    for match in re.finditer(PHONE_REGEX, masked_text):
        if match.group(0) not in found_pii:
            masked_text = masked_text.replace(match.group(0), "[PHONE_NUMBER]", 1)
            found_pii.add(match.group(0))

    # SpaCy-based masking
    doc = nlp(masked_text)
    pii_labels = {"PERSON", "GPE", "LOC", "ORG"}
    
    for ent in doc.ents:
        if ent.label_ in pii_labels and ent.text not in found_pii:
            masked_text = masked_text.replace(ent.text, f"[{ent.label_}]")
            found_pii.add(ent.text)

    # THIS IS THE CORRECTED RETURN STATEMENT
    return jsonify({'masked_text': masked_text})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)