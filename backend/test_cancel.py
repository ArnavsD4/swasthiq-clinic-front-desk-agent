from data_loader import load_clinic_data
from tools.cancel import cancel_appointment


# --------------------------------------------------
# TEST 1: Successful cancellation
# --------------------------------------------------

clinic_data = load_clinic_data()

appointment = clinic_data["appointments"][0]

result = cancel_appointment(
    clinic_data,
    appointment["id"],
    appointment["patient_id"]
)

print("\nTEST 1 - Successful cancellation")
print(result)


# --------------------------------------------------
# TEST 2: Appointment not found
# --------------------------------------------------

clinic_data = load_clinic_data()

result = cancel_appointment(
    clinic_data,
    "ap_9999",
    "pt_0001"
)

print("\nTEST 2 - Appointment not found")
print(result)


# --------------------------------------------------
# TEST 3: Wrong patient
# --------------------------------------------------

clinic_data = load_clinic_data()

appointment = clinic_data["appointments"][0]

result = cancel_appointment(
    clinic_data,
    appointment["id"],
    "pt_9999"
)

print("\nTEST 3 - Wrong patient")
print(result)


# --------------------------------------------------
# TEST 4: Already cancelled appointment
# --------------------------------------------------

clinic_data = load_clinic_data()

appointment = clinic_data["appointments"][0]

# First cancellation
cancel_appointment(
    clinic_data,
    appointment["id"],
    appointment["patient_id"]
)

# Second cancellation
result = cancel_appointment(
    clinic_data,
    appointment["id"],
    appointment["patient_id"]
)

print("\nTEST 4 - Already cancelled")
print(result)


# --------------------------------------------------
# TEST 5: Appointment status actually changes
# --------------------------------------------------

clinic_data = load_clinic_data()

appointment = clinic_data["appointments"][0]

print("\nTEST 5 - Status change")

print("Before:", appointment["status"])

cancel_appointment(
    clinic_data,
    appointment["id"],
    appointment["patient_id"]
)

print("After:", appointment["status"])


# --------------------------------------------------
# TEST 6: Cancelled appointment should no longer
#          be treated as a booked slot
# --------------------------------------------------

clinic_data = load_clinic_data()

appointment = clinic_data["appointments"][0]

print("\nTEST 6 - Cancelled appointment is no longer booked")

print("Appointment before cancellation:")
print(appointment)

cancel_appointment(
    clinic_data,
    appointment["id"],
    appointment["patient_id"]
)

print("\nAppointment after cancellation:")
print(appointment)

print("\nStatus:", appointment["status"])