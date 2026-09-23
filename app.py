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

# --- UPDATED: Search by Disease Name instead of Crop Name ---
def get_disease_by_name(disease_input):
    if not os.path.exists(DB_PATH):
        return None
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Use wildcard search to reliably match disease names regardless of case
    search_pattern = f"%{disease_input.strip()}%"
    
    # Fetch exact disease data along with newly separated organic and chemical treatments
    cur.execute("""
        SELECT d.disease_name, c.crop_name, p.type_name as pathogen, 
               d.causal_organism, d.symptoms, d.organic_treatment, d.chemical_treatment 
        FROM diseases d
        JOIN crops c ON d.crop_id = c.crop_id
        JOIN pathogen_types p ON d.pathogen_type_id = p.pathogen_type_id
        WHERE d.disease_name LIKE ?
        LIMIT 1
    """, (search_pattern,))
    
    row = cur.fetchone()
    
    # Fallback to the first available record if no match is found
    if not row:
        cur.execute("""
            SELECT d.disease_name, c.crop_name, p.type_name as pathogen, 
                   d.causal_organism, d.symptoms, d.organic_treatment, d.chemical_treatment 
            FROM diseases d
            JOIN crops c ON d.crop_id = c.crop_id
            JOIN pathogen_types p ON d.pathogen_type_id = p.pathogen_type_id
            LIMIT 1
        """)
        row = cur.fetchone()
        
    conn.close()
    return dict(row) if row else None

# Simulated NGO geospatial lookup function
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
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'Empty file name'}), 400

    # Capture location from the frontend (Crop is no longer sent!)
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    
    # ==========================================
    # --- SIMULATED AI COMPUTER VISION LAYER ---
    # ==========================================
    # In a real deployment, the uploaded 'file' pixels would be analyzed by your ML model here.
    # The model predicts the disease directly:
    predicted_ai_disease = 'Tomato Early Blight'
    
    print(f"👉 DEBUG: AI Model predicted [{predicted_ai_disease}] at GPS: {latitude}, {longitude}")
    
    # Query the SQLite database using the AI's disease prediction
    disease_record = get_disease_by_name(predicted_ai_disease)

    if not disease_record:
        disease_record = {
            'disease_name': 'Unknown Disease',
            'crop_name': 'Unknown',
            'symptoms': 'Scan inconclusive.',
            'organic_treatment': 'Consult local agricultural expert.',
            'chemical_treatment': 'Consult local agricultural expert.'
        }

    # Determine NGO proximity if coordinates were provided
    ngo_notified = False
    ngo_details = None
    
    if latitude and longitude:
        ngo_notified = True
        ngo_details = get_nearest_ngo(float(latitude), float(longitude))

    # Construct JSON payload with dynamic database results
    response_payload = {
        'status': 'success',
        'disease': disease_record['disease_name'],
        'raw_disease': disease_record['disease_name'],
        'crop': disease_record['crop_name'], # Crop is now automatically mapped by the database
        'symptoms': disease_record['symptoms'],
        'organic_treatment': disease_record['organic_treatment'],
        'chemical_treatment': disease_record['chemical_treatment'],
        'severity': 85,
        'ngo_notified': ngo_notified,
        'ngo_details': ngo_details
    }
    
    return jsonify(response_payload)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)