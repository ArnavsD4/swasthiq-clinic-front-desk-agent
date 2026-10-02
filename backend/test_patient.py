from data_loader import load_clinic_data
from tools.patient import lookup_patient

data = load_clinic_data()
patients = data["patients"]

print("\n--- TEST 1: Unique Patient ---")

result = lookup_patient(
    patients,
    name = "Rajesh Kumar Sharma"
)

print(result)


print("\n--- TEST 2: Ambigous Patient ---")

result = lookup_patient(
    patients,
    name="Sharma"
)

print(result)

print("\n--- TEST 3: Patient not found ---")

result = lookup_patient(
    patients,
    name="Rahul XYZ"
)

print(result)

print("\n--- TEST 4: Name + phone ---")

result = lookup_patient(
    patients,
    name="Sharma",
    phone="9812200011"
)

print(result)


print("\n--- TEST 5: Name + DOB ---")

result = lookup_patient(
    patients,
    name="Sharma",
    dob="1988-11-02"
)

print(result)