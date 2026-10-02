from data_loader import load_clinic_data
from tools.booking import book_appointment

clinic_data = load_clinic_data()

patient_id = clinic_data["patients"][0]["id"]

result = book_appointment(
    clinic_data,
    patient_id,
    "dr_rao",
    "2026-10-01",
    "11:00",
    "11:15"
)

print("\nTEST 1 - Successful booking")
print(result)

clinic_data = load_clinic_data()

result = book_appointment(
    clinic_data,
    "pt_9999",
    "dr_rao",
    "2026-10-01",
    "11:00",
    "11:15"
)

print("\nTEST 2 - Invalid patient")
print(result)

clinic_data = load_clinic_data()

patient_id = clinic_data["patients"][0]["id"]

result = book_appointment(
    clinic_data,
    patient_id,
    "dr_fake",
    "2026-10-01",
    "11:00",
    "11:15"
)

print("\nTEST 3 - Invalid doctor")
print(result)

clinic_data = load_clinic_data()

result = book_appointment(
    clinic_data,
    patient_id,
    "dr_rao",
    "2026-99-99",
    "11:00",
    "11:15"
)

print("\nTEST 4 - Invalid date")
print(result)

clinic_data = load_clinic_data()

result = book_appointment(
    clinic_data,
    patient_id,
    "dr_rao",
    "2026-10-02",
    "11:00",
    "11:15"
)

print("\nTEST 5 - Holiday")
print(result)

clinic_data = load_clinic_data()

result = book_appointment(
    clinic_data,
    patient_id,
    "dr_rao",
    "2026-10-04",
    "11:00",
    "11:15"
)

print("\nTEST 6 - Doctor not working")
print(result)

clinic_data = load_clinic_data()

result = book_appointment(
    clinic_data,
    patient_id,
    "dr_rao",
    "2026-10-01",
    "11:07",
    "11:22"
)

print("\nTEST 7 - Invalid slot")
print(result)

clinic_data = load_clinic_data()

result = book_appointment(
    clinic_data,
    patient_id,
    "dr_rao",
    "2026-10-01",
    "09:30",
    "09:45"
)

print("\nTEST 8 - Already booked slot")
print(result)

clinic_data = load_clinic_data()

before = len(clinic_data["appointments"])

result = book_appointment(
    clinic_data,
    patient_id,
    "dr_rao",
    "2026-10-01",
    "11:15",
    "11:30"
)

after = len(clinic_data["appointments"])

print("\nTEST 9 - Appointment added")
print("Before:", before)
print("After:", after)
print(result)

clinic_data = load_clinic_data()

first = book_appointment(
    clinic_data,
    patient_id,
    "dr_rao",
    "2026-10-01",
    "11:30",
    "11:45"
)

second = book_appointment(
    clinic_data,
    patient_id,
    "dr_rao",
    "2026-10-01",
    "11:30",
    "11:45"
)

print("\nTEST 10 - Same slot twice")
print("First booking:")
print(first)

print("Second booking:")
print(second)

print("\nTEST 11 - Invalid start time")

result = book_appointment(
    clinic_data,
    "pt_0001",
    "dr_rao",
    "2026-10-01",
    "abc",
    "11:15"
)

print(result)


print("\nTEST 12 - Invalid end time")

result = book_appointment(
    clinic_data,
    "pt_0001",
    "dr_rao",
    "2026-10-01",
    "11:00",
    "xyz"
)

print(result)


print("\nTEST 13 - Invalid time format")

result = book_appointment(
    clinic_data,
    "pt_0001",
    "dr_rao",
    "2026-10-01",
    "25:90",
    "26:00"
)

print(result)

print("\nTEST 14 - Start time after end time")

result = book_appointment(
    clinic_data,
    "pt_0001",
    "dr_rao",
    "2026-10-01",
    "11:30",
    "11:15"
)

print(result)


print("\nTEST 15 - Start time equals end time")

result = book_appointment(
    clinic_data,
    "pt_0001",
    "dr_rao",
    "2026-10-01",
    "11:15",
    "11:15"
)

print(result)