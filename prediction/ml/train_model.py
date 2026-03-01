import pandas as pd
import pickle
from sklearn.ensemble import RandomForestClassifier

# Load dataset
df = pd.read_csv("../data/master_healthcare_dataset.csv")

# Separate features & target
X = df[[col for col in df.columns if col.startswith("symptom_")]]
y = df["disease_name"]

# Train model
model = RandomForestClassifier(
    n_estimators=200,
    random_state=42
)
model.fit(X, y)

# Save model
with open("disease_model.pkl", "wb") as f:
    pickle.dump(model, f)

print("✅ Model trained and saved successfully")
