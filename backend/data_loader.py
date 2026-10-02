import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CLINIC_FILE = BASE_DIR / "clinic.json"

def load_clinic_data():
    with open(CLINIC_FILE, "r") as file:
        return json.load(file)

# with open("clinic.json", "r") as file:
#     clinic_data = json.load(file)

# print(clinic_data["patients"][0])