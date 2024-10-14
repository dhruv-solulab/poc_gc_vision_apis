from flask import Flask, render_template, request, jsonify
import os
import json
import re
from google.cloud import vision
from googletrans import Translator

app = Flask(__name__)

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'C:\\Users\\USER\\Desktop\\Internship\\NER_Amanbank\\google_cloud_vision\\numeric-skill-430508-k7-cd9f0bb33676.json'

vision_client = vision.ImageAnnotatorClient()
translator = Translator()

def perform_ocr_and_translate(image_path, target_language):
    with open(image_path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    response = vision_client.text_detection(image=image)
    texts = response.text_annotations

    output = {
        'detected_text': None,
        'translated_text': None,
        'error': None,
        'extracted_entities': None
    }

    if texts:
        detected_text = texts[0].description
        output['detected_text'] = detected_text

        translated_text = translator.translate(detected_text, dest=target_language)
        output['translated_text'] = translated_text.text

        entities = extract_entities(detected_text)
        output['extracted_entities'] = entities
    else:
        output['error'] = "No text detected."

    if response.error.message:
        output['error'] = response.error.message
        raise Exception(f'{response.error.message}')

    return json.dumps(output, ensure_ascii=False, indent=4)

def extract_entities(text):
    entities = {
        "NAME": None,
        "ENGINE_NUMBER": None,
        "CHASSIS_NUMBER": None,
        "INSURANCE_NUMBER": None,
        "INSURANCE_EXPIRY": None,
        "YEAR_OF_MANUFACTURE": None,
    }

    patterns = {
        "INSURANCE_NUMBER": r"(?:رقم الوثيقة|Document number)\s*([0-9]+)",
        "INSURANCE_EXPIRY": r"(?:انتهاء التأمين|Insurance ends)\s*([0-9]{2}-[0-9]{2}-[0-9]{4})",
        "YEAR_OF_MANUFACTURE": r"(?:سنة الصنع|The year of manufacture)\s*([0-9]{4})",
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            entities[key] = match.group(1).strip()

    engine_number_pattern = r"\b([A-Z0-9]{13})\b"
    chassis_number_pattern = r"رقم المحرك\s*([A-Z0-9]+)"
    
    engine_match = re.search(engine_number_pattern, text)
    chassis_match = re.search(chassis_number_pattern, text)
    
    if engine_match:
        entities["ENGINE_NUMBER"] = engine_match.group(1).strip()
    if chassis_match:
        entities["CHASSIS_NUMBER"] = chassis_match.group(1).strip()

    return entities

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_image():
    image = request.files['image']
    language = request.form.get('language')
    
    if image and language:
        image_path = f'./uploaded_images/{image.filename}'
        image.save(image_path)
        
        try:
            result = perform_ocr_and_translate(image_path, language)
            return jsonify(result=json.loads(result))
        except Exception as e:
            return jsonify({'error': str(e)})
    return jsonify({'error': 'Invalid input'})

if __name__ == '__main__':
    app.run(debug=True)
