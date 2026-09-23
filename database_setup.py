import sqlite3
import os

DB_PATH = "crop_diseases.db"
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# 1. Create Tables (Updated with separate organic and chemical treatments)
cur.executescript("""
CREATE TABLE crops (
    crop_id INTEGER PRIMARY KEY AUTOINCREMENT,
    crop_name TEXT NOT NULL UNIQUE,
    crop_category TEXT
);

CREATE TABLE pathogen_types (
    pathogen_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_name TEXT NOT NULL UNIQUE
);

CREATE TABLE diseases (
    disease_id INTEGER PRIMARY KEY AUTOINCREMENT,
    disease_name TEXT NOT NULL,
    crop_id INTEGER NOT NULL,
    pathogen_type_id INTEGER NOT NULL,
    causal_organism TEXT,
    symptoms TEXT,
    favorable_conditions TEXT,
    transmission TEXT,
    organic_treatment TEXT,
    chemical_treatment TEXT,
    FOREIGN KEY (crop_id) REFERENCES crops(crop_id),
    FOREIGN KEY (pathogen_type_id) REFERENCES pathogen_types(pathogen_type_id)
);

CREATE INDEX idx_diseases_crop ON diseases(crop_id);
CREATE INDEX idx_diseases_pathogen_type ON diseases(pathogen_type_id);
""")

# 2. Insert Pathogen Types
pathogen_types = ["Fungal", "Bacterial", "Viral", "Nematode", "Phytoplasma", "Oomycete (Water Mold)"]
cur.executemany("INSERT INTO pathogen_types (type_name) VALUES (?)", [(p,) for p in pathogen_types])
conn.commit()

# 3. Insert Crops
crops_data = [
    ("Rice", "Cereal"), ("Wheat", "Cereal"), ("Maize", "Cereal"), ("Tomato", "Vegetable"),
    ("Potato", "Vegetable"), ("Onion", "Vegetable"), ("Sugarcane", "Cash Crop"), ("Soybean", "Legume/Oilseed")
]
cur.executemany("INSERT INTO crops (crop_name, crop_category) VALUES (?, ?)", crops_data)
conn.commit()

# Create lookup maps for IDs
crop_map = {name: cid for cid, name in cur.execute("SELECT crop_id, crop_name FROM crops")}
ptype_map = {name: pid for pid, name in cur.execute("SELECT pathogen_type_id, type_name FROM pathogen_types")}

# 4. Insert Diseases (Aligned exactly with your HTML frontend translations)
diseases = [
    ("Rice Blast", "Rice", "Fungal", "Magnaporthe oryzae",
     "Spindle-shaped lesions with grey centers and brown margins on leaves; neck and node rot causing white panicles.",
     "High humidity, extended leaf wetness, temperatures of 25-28°C",
     "Airborne spores, infected seed",
     "Avoid excessive nitrogen fertilization and use resistant seed varieties.",
     "Spray Tricyclazole 75% WP @ 0.6g per liter of water."),
     
    ("Wheat Rust (Stem/Black Rust)", "Wheat", "Fungal", "Puccinia graminis f. sp. tritici",
     "Reddish-brown pustules on stems and leaves rupturing epidermis, turning black later.",
     "Warm days (18-25°C), cool nights, high humidity",
     "Wind-dispersed spores",
     "Plant rust-resistant cultivars and remove alternate weed hosts.",
     "Spray Propiconazole 25% EC @ 1ml per liter of water."),
     
    ("Tomato Early Blight", "Tomato", "Fungal", "Alternaria solani",
     "Concentric ring lesions on older leaves, stem cankers, fruit rot near stem end.",
     "Warm humid weather, alternating wet-dry periods",
     "Airborne conidia, infected debris",
     "Crop rotation, resistant varieties, and biological neem formulations.",
     "Spray Mancozeb or Chlorothalonil @ 2.5g per liter."),
     
    ("Potato Early Blight", "Potato", "Fungal", "Alternaria solani",
     "Concentric ring lesions on older leaves, yellowing and premature leaf drop.",
     "Warm humid weather, alternating wet-dry periods",
     "Airborne spores, soil-borne debris",
     "Apply targeted Neem oil extract (5ml/liter) and maintain proper crop rotation.",
     "Spray Mancozeb 75% WP @ 2.5g per liter of water."),
     
    ("Sugarcane Red Rot", "Sugarcane", "Fungal", "Colletotrichum falcatum",
     "Reddening of internal stalk tissue with white transverse patches, drying of leaves, alcoholic smell.",
     "Warm humid weather, waterlogging",
     "Infected setts, soil-borne",
     "Select disease-free setts from certified nurseries and treat with hot water.",
     "Dip setts in Carbendazim 50% WP @ 1g per liter solution.")
]

rows = []
for name, crop, ptype, organism, symptoms, conditions, transmission, organic, chemical in diseases:
    if crop in crop_map and ptype in ptype_map:
        rows.append((name, crop_map[crop], ptype_map[ptype], organism, symptoms, conditions, transmission, organic, chemical))

cur.executemany("""
INSERT INTO diseases
(disease_name, crop_id, pathogen_type_id, causal_organism, symptoms, favorable_conditions, transmission, organic_treatment, chemical_treatment)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", rows)

conn.commit()
conn.close()

print("Database 'crop_diseases.db' successfully created and seeded with Frontend-synced data!")