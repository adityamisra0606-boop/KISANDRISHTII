import sqlite3
import os

DB_PATH = "crop_diseases.db"
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

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
    management TEXT,
    FOREIGN KEY (crop_id) REFERENCES crops(crop_id),
    FOREIGN KEY (pathogen_type_id) REFERENCES pathogen_types(pathogen_type_id)
);

CREATE INDEX idx_diseases_crop ON diseases(crop_id);
CREATE INDEX idx_diseases_pathogen_type ON diseases(pathogen_type_id);
""")

pathogen_types = ["Fungal", "Bacterial", "Viral", "Nematode", "Phytoplasma", "Oomycete (Water Mold)"]
cur.executemany("INSERT INTO pathogen_types (type_name) VALUES (?)", [(p,) for p in pathogen_types])
conn.commit()

crop_map = {name: cid for cid, name in cur.execute("SELECT crop_id, crop_name FROM crops")}

crops_data = [
    ("Rice", "Cereal"), ("Wheat", "Cereal"), ("Maize", "Cereal"), ("Tomato", "Vegetable"),
    ("Potato", "Vegetable"), ("Onion", "Vegetable"), ("Sugarcane", "Cash Crop"), ("Soybean", "Legume/Oilseed")
]
cur.executemany("INSERT INTO crops (crop_name, crop_category) VALUES (?, ?)", crops_data)
conn.commit()

crop_map = {name: cid for cid, name in cur.execute("SELECT crop_id, crop_name FROM crops")}
ptype_map = {name: pid for pid, name in cur.execute("SELECT pathogen_type_id, type_name FROM pathogen_types")}

diseases = [
    ("Rice Blast", "Rice", "Fungal", "Magnaporthe oryzae",
     "Spindle-shaped lesions with grey centers and brown margins on leaves; neck and node rot causing white panicles",
     "High humidity, extended leaf wetness, temperatures of 25-28°C, excess nitrogen",
     "Airborne spores, infected seed and stubble",
     "Resistant varieties, balanced nitrogen use, fungicides (tricyclazole, azoxystrobin), field sanitation"),
    ("Wheat Rust (Stem/Black Rust)", "Wheat", "Fungal", "Puccinia graminis f. sp. tritici",
     "Reddish-brown pustules on stems and leaves rupturing epidermis, turning black later",
     "Warm days (18-25°C), cool nights, high humidity, dew",
     "Wind-dispersed urediniospores",
     "Resistant varieties, fungicide sprays (propiconazole), early sowing, removal of alternate hosts"),
    ("Tomato Early Blight", "Tomato", "Fungal", "Alternaria solani",
     "Concentric ring (target-board) lesions on older leaves, stem cankers, fruit rot near stem end",
     "Warm humid weather, alternating wet-dry periods",
     "Airborne/splash-dispersed conidia, infected debris",
     "Crop rotation, resistant varieties, fungicides (mancozeb, chlorothalonil)"),
    ("Potato Late Blight", "Potato", "Oomycete (Water Mold)", "Phytophthora infestans",
     "Dark water-soaked lesions on leaves with white mold ring underneath, tuber rot with reddish-brown discoloration",
     "Cool moist weather, high humidity, temperatures 15-20°C",
     "Airborne sporangia, infected seed tubers",
     "Certified disease-free seed, fungicides, resistant varieties, destroy volunteer plants"),
    ("Sugarcane Red Rot", "Sugarcane", "Fungal", "Colletotrichum falcatum",
     "Reddening of internal stalk tissue with white patches, drying of leaves, alcoholic smell in cane",
     "Warm humid weather, waterlogging, use of infected setts",
     "Infected setts, soil-borne, wind-dispersed spores",
     "Resistant varieties, disease-free setts, hot water treatment of setts, field sanitation")
]

rows = []
for name, crop, ptype, organism, symptoms, conditions, transmission, mgmt in diseases:
    if crop in crop_map and ptype in ptype_map:
        rows.append((name, crop_map[crop], ptype_map[ptype], organism, symptoms, conditions, transmission, mgmt))

cur.executemany("""
INSERT INTO diseases
(disease_name, crop_id, pathogen_type_id, causal_organism, symptoms, favorable_conditions, transmission, management)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", rows)
conn.commit()
conn.close()

print("Database 'crop_diseases.db' successfully created and seeded!")