import pandas as pd
import os
import pickle
import re
from django.conf import settings

# Load dataset
DATASET_PATH = os.path.join(
    settings.BASE_DIR,
    "prediction",
    "data",
    "master_healthcare_dataset.csv"
)
df = pd.read_csv(DATASET_PATH)

SYMPTOM_COLUMNS = [c for c in df.columns if c.startswith("symptom_")]
SYMPTOM_NAMES = [c.replace("symptom_", "").replace("_", " ") for c in SYMPTOM_COLUMNS]

# Load ML model once
MODEL_PATH = os.path.join(
    settings.BASE_DIR,
    "prediction",
    "ml",
    "disease_model.pkl"
)

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)


def normalize_text(value):
    return re.sub(r"[^a-z0-9\s]+", " ", str(value).lower()).strip()


DISEASE_LOOKUP = {
    normalize_text(row["disease_name"]): row
    for _, row in df.iterrows()
}


def get_disease_details(disease_name):
    row = DISEASE_LOOKUP.get(normalize_text(disease_name))
    if row is None:
        return None

    return {
        "disease": row["disease_name"],
        "severity": row["severity"],
        "remedy": row["household_remedies"],
        "advice": row["doctor_visit_advice"],
    }

def predict_disease_from_symptoms(selected_symptoms):
    # Create empty input row
    input_data = dict.fromkeys(SYMPTOM_COLUMNS, 0)

    # Convert symptoms to column format
    for s in selected_symptoms:
        col = "symptom_" + s.lower().replace(" ", "_")
        if col in input_data:
            input_data[col] = 1

    # Convert to DataFrame
    X_input = pd.DataFrame([input_data])

    # Predict disease
    predicted_disease = model.predict(X_input)[0]

    result = get_disease_details(predicted_disease)
    if result is None:
        return None

    return result
