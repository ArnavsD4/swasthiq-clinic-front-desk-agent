from data_loader import load_clinic_data

data = load_clinic_data()

print("\n--- HOLIDAYS ---")
print(data["holidays"])

print("\n--- APPOINTMENTS ---")
for appointment in data["appointments"]:
    print(appointment)