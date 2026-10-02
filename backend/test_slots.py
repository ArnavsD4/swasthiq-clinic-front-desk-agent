# from tools.slots import time_to_minutes, minutes_to_time

# print(time_to_minutes("09:00"))
# print(time_to_minutes("09:30"))
# print(time_to_minutes("10:00"))

# print(minutes_to_time(540))
# print(minutes_to_time(570))
# print(minutes_to_time(615))

from data_loader import load_clinic_data
from tools.slots import (
    time_to_minutes,
    minutes_to_time,
    find_doctor,
    get_day_name,
    get_working_windows,
    generate_slots,
    get_booked_slots,
    remove_booked_slots,
    search_slots
)

data = load_clinic_data()


print("--- TIME TEST ---")
print(time_to_minutes("09:30"))
print(minutes_to_time(570))


print("\n--- DOCTOR TEST ---")
doctor = find_doctor(data, "dr_rao")
print(doctor["name"])

print("\n--- DAY TEST ---")
print(get_day_name("2026-10-01"))

print("\n--- WORKING WINDOWS TEST ---")

doctor = find_doctor(data, "dr_rao")
day = get_day_name("2026-10-01")

windows = get_working_windows(doctor, day)

print(windows)

print("\n--- GENERATE SLOTS ---")

doctor = find_doctor(data, "dr_rao")
day = get_day_name("2026-10-01")

windows = get_working_windows(doctor, day)

slots = generate_slots(
    windows,
    data["clinic"]["slot_minutes"]
)

for slot in slots:
    print(slot)

print("\n--- REMOVE BOOKED SLOTS ---")

booked_slots = get_booked_slots(
    data,
    "dr_rao",
    "2026-10-01"
)

print("Booked:")
print(booked_slots)

print("\nTotal slots:", len(slots))
print("Unique slots:", len(set(
    (slot["start"], slot["end"])
    for slot in slots
)))

available_slots = remove_booked_slots(
    slots,
    booked_slots
)

print("\nAvailable:")
for slot in available_slots:
    print(slot)

print("\n--- SEARCH SLOTS ---")

result = search_slots(
    data,
    "dr_rao",
    "2026-10-01"
)

print(result)

print("\n--- HOLDIAY TEST ---")

print(
    search_slots(
        data,
        "dr_rao",
        "2026-10-02"
    )
)

print("\n--- INVALID DOCTOR TEST ---")

print(
    search_slots(
        data,
        "dr_fake",
        "2026-10-01"
    )
)

print("\nTEST - Invalid date")

result = search_slots(
     data,
    "dr_rao",
    "2026-99-99"
)

print(result)