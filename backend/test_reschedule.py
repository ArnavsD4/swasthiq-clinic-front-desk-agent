from data_loader import load_clinic_data
from tools.reschedule import reschedule_appointment


# --------------------------------------------------
# TEST 1: Successful reschedule
# --------------------------------------------------

clinic_data = load_clinic_data()

appointment = clinic_data["appointments"][0]

result = reschedule_appointment(
    clinic_data,
    appointment["id"],
    appointment["patient_id"],
    "2026-10-01",
    "11:00",
    "11:15"
)

print("\nTEST 1 - Successful reschedule")
print(result)


# --------------------------------------------------
# TEST 2: Appointment not found
# --------------------------------------------------

clinic_data = load_clinic_data()

result = reschedule_appointment(
    clinic_data,
    "ap_9999",
    "pt_0001",
    "2026-10-01",
    "11:00",
    "11:15"
)

print("\nTEST 2 - Appointment not found")
print(result)


# --------------------------------------------------
# TEST 3: Wrong patient
# --------------------------------------------------

clinic_data = load_clinic_data()

appointment = clinic_data["appointments"][0]

result = reschedule_appointment(
    clinic_data,
    appointment["id"],
    "pt_9999",
    "2026-10-01",
    "11:00",
    "11:15"
)

print("\nTEST 3 - Wrong patient")
print(result)


# --------------------------------------------------
# TEST 4: Invalid date
# --------------------------------------------------

clinic_data = load_clinic_data()

appointment = clinic_data["appointments"][0]

result = reschedule_appointment(
    clinic_data,
    appointment["id"],
    appointment["patient_id"],
    "2026-99-99",
    "11:00",
    "11:15"
)

print("\nTEST 4 - Invalid date")
print(result)


# --------------------------------------------------
# TEST 5: Holiday
# --------------------------------------------------

clinic_data = load_clinic_data()

appointment = clinic_data["appointments"][0]

result = reschedule_appointment(
    clinic_data,
    appointment["id"],
    appointment["patient_id"],
    "2026-10-02",
    "11:00",
    "11:15"
)

print("\nTEST 5 - Holiday")
print(result)


# --------------------------------------------------
# TEST 6: Doctor not working
# --------------------------------------------------

clinic_data = load_clinic_data()

appointment = clinic_data["appointments"][0]

result = reschedule_appointment(
    clinic_data,
    appointment["id"],
    appointment["patient_id"],
    "2026-10-04",
    "11:00",
    "11:15"
)

print("\nTEST 6 - Doctor not working")
print(result)


# --------------------------------------------------
# TEST 7: Invalid slot
# --------------------------------------------------

clinic_data = load_clinic_data()

appointment = clinic_data["appointments"][0]

result = reschedule_appointment(
    clinic_data,
    appointment["id"],
    appointment["patient_id"],
    "2026-10-01",
    "11:07",
    "11:22"
)

print("\nTEST 7 - Invalid slot")
print(result)


# --------------------------------------------------
# TEST 8: Already booked slot
# --------------------------------------------------

clinic_data = load_clinic_data()

appointment = clinic_data["appointments"][0]

result = reschedule_appointment(
    clinic_data,
    appointment["id"],
    appointment["patient_id"],
    "2026-10-01",
    "10:00",
    "10:15"
)

print("\nTEST 8 - Already booked slot")
print(result)


# --------------------------------------------------
# TEST 9: Cancelled appointment cannot be rescheduled
# --------------------------------------------------

clinic_data = load_clinic_data()

appointment = clinic_data["appointments"][0]

# Temporarily make it cancelled
appointment["status"] = "cancelled"

result = reschedule_appointment(
    clinic_data,
    appointment["id"],
    appointment["patient_id"],
    "2026-10-01",
    "11:00",
    "11:15"
)

print("\nTEST 9 - Cancelled appointment")
print(result)


# --------------------------------------------------
# TEST 10: Original appointment remains same ID
# --------------------------------------------------

clinic_data = load_clinic_data()

appointment = clinic_data["appointments"][0]

original_id = appointment["id"]

result = reschedule_appointment(
    clinic_data,
    appointment["id"],
    appointment["patient_id"],
    "2026-10-01",
    "11:00",
    "11:15"
)

print("\nTEST 10 - Appointment ID remains same")
print("Original ID:", original_id)
print("Updated ID:", result["appointment"]["id"])

print("\nTEST 11 - Invalid new start time")

clinic_data = load_clinic_data()

result = reschedule_appointment(
    clinic_data,
    "ap_0001",
    "pt_0001",
    "2026-10-01",
    "abc",
    "11:15"
)

print(result)


print("\nTEST 12 - Invalid new end time")

clinic_data = load_clinic_data()

result = reschedule_appointment(
    clinic_data,
    "ap_0001",
    "pt_0001",
    "2026-10-01",
    "11:00",
    "xyz"
)

print(result)


print("\nTEST 13 - Start after end")

clinic_data = load_clinic_data()

result = reschedule_appointment(
    clinic_data,
    "ap_0001",
    "pt_0001",
    "2026-10-01",
    "11:30",
    "11:15"
)

print(result)