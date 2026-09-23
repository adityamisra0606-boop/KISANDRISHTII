import os
import io
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import sqlite3
from gtts import gTTS

app = Flask(__name__)
CORS(app)

app.config['TEMPLATES_AUTO_RELOAD'] = True
DB_PATH = "crop_diseases.db"

def get_disease_by_crop_name(crop_input):
    if not os.path.exists(DB_PATH):
        return None
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Use wildcard search (%crop%) to reliably match crop names regardless of case or spacing
    search_pattern = f"%{crop_input.strip()}%"
    cur.execute("""
        SELECT d.disease_name, c.crop_name, p.type_name as pathogen, 
               d.causal_organism, d.symptoms, d.management 
        FROM diseases d
        JOIN crops c ON d.crop_id = c.crop_id
        JOIN pathogen_types p ON d.pathogen_type_id = p.pathogen_type_id
        WHERE c.crop_name LIKE ?
        LIMIT 1
    """, (search_pattern,))
    
    row = cur.fetchone()
    
    # Fallback to the first available record if no match is found
    if not row:
        cur.execute("""
            SELECT d.disease_name, c.crop_name, p.type_name as pathogen, 
                   d.causal_organism, d.symptoms, d.management 
            FROM diseases d
            JOIN crops c ON d.crop_id = c.crop_id
            JOIN pathogen_types p ON d.pathogen_type_id = p.pathogen_type_id
            LIMIT 1
        """)
        row = cur.fetchone()
        
    conn.close()
    return dict(row) if row else None

# Added simulated NGO geospatial lookup function
def get_nearest_ngo(lat, lon):
    return {
        "name": "Kisan Sahayata Kendra (Block Field Office)",
        "contact": "+91-1800-120-4040"
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/tts', methods=['POST'])
def text_to_speech():
    data = request.get_json()
    text = data.get('text', '')
    lang = data.get('lang', 'bn')

    if not text:
        return jsonify({'error': 'No text provided'}), 400

    try:
        tts = gTTS(text=text, lang=lang)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return send_file(fp, mimetype='audio/mp3')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analyze', methods=['POST'])
def analyze():
    # 1. CHANGED: Match frontend key 'image' instead of 'file'
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'Empty file name'}), 400

    # 2. CHANGED: Capture latitude, longitude, and crop from FormData
    selected_crop = request.form.get('crop', 'tomato')
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    
    print(f"👉 DEBUG: Scan initiated for [{selected_crop}] at GPS: {latitude}, {longitude}")
    
    disease_record = get_disease_by_crop_name(selected_crop)

    if not disease_record:
        disease_record = {
            'disease_name': 'Tomato Early Blight',
            'crop_name': 'Tomato',
            'pathogen': 'Fungal',
            'symptoms': 'Concentric ring lesions on older leaves, stem cankers, fruit rot near stem end.',
            'management': 'Spray Mancozeb or Chlorothalonil @ 2.5g per liter and enforce crop rotation.'
        }

    # 3. CHANGED: Determine NGO proximity if coordinates were provided
    ngo_notified = False
    ngo_details = None
    
    if latitude and longitude:
        ngo_notified = True
        ngo_details = get_nearest_ngo(float(latitude), float(longitude))

    # 4. CHANGED: Map response keys exactly to the updated frontend requirements
    response_payload = {
        'status': 'success',
        'disease': disease_record['disease_name'],
        'raw_disease': disease_record['disease_name'],
        'crop': disease_record['crop_name'],
        'symptoms': disease_record['symptoms'],
        'chemical_treatment': disease_record['management'],
        'organic_treatment': 'Apply certified organic neem formulation as baseline defense.',
        'severity': 78,
        'ngo_notified': ngo_notified,
        'ngo_details': ngo_details
    }
    
    return jsonify(response_payload)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)