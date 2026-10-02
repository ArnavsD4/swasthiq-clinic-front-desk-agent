from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from data_loader import load_clinic_data
from tools.booking import book_appointment


# Every thread must use the SAME data object.
data = load_clinic_data()

TOTAL_REQUESTS = 10

# Makes the threads start their booking attempts together.
barrier = Barrier(TOTAL_REQUESTS)


def attempt_booking(request_number):

    barrier.wait()

    result = book_appointment(
        data,
        "pt_0001",
        "dr_rao",
        "2026-10-01",
        "11:00",
        "11:15"
    )

    return result


# Send 10 booking requests concurrently.
with ThreadPoolExecutor(max_workers=TOTAL_REQUESTS) as executor:

    results = list(
        executor.map(
            attempt_booking,
            range(TOTAL_REQUESTS)
        )
    )


successful = [
    result
    for result in results
    if result["status"] == "booked"
]

failed = [
    result
    for result in results
    if result["status"] != "booked"
]


print("\n--- RACE CONDITION TEST ---")

print("Total requests:", len(results))
print("Successful bookings:", len(successful))
print("Failed bookings:", len(failed))


print("\n--- INDIVIDUAL RESULTS ---")

for index, result in enumerate(results, start=1):
    print(f"Request {index}: {result['status']}")


print("\n--- FINAL APPOINTMENT CHECK ---")

matching_appointments = [
    appointment
    for appointment in data["appointments"]
    if (
        appointment["doctor_id"] == "dr_rao"
        and appointment["date"] == "2026-10-01"
        and appointment["start"] == "11:00"
        and appointment["end"] == "11:15"
        and appointment["status"] == "booked"
    )
]

print(
    "Appointments occupying requested slot:",
    len(matching_appointments)
)


assert len(successful) == 1, "Race condition detected!"
assert len(failed) == 9, "Unexpected booking results!"
assert len(matching_appointments) == 1, "Double booking detected!"

print("\nRACE CONDITION TEST PASSED!")