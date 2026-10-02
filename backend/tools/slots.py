from datetime import datetime

def time_to_minutes(time_string):
    hours, minutes = map(int, time_string.split(":"))
    return hours * 60 + minutes

def minutes_to_time(total_minutes):
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours:02d}:{minutes:02d}"

def find_doctor(clinic_data, doctor_id):
    for doctor in clinic_data["doctors"]:
        if doctor["id"] == doctor_id:
            return doctor

    return None

def get_day_name(date):
    requested_date = datetime.strptime(date, "%Y-%m-%d")
    return requested_date.strftime("%a")

def get_working_windows(doctor, day_name):
    windows = []

    for window in doctor["windows"]:
        if window["day"] == day_name:
            windows.append(window)

    return windows

def generate_slots(windows, slot_minutes):
    slots = []

    for window in windows:
        start = time_to_minutes(window["start"])
        end = time_to_minutes(window["end"])

        current = start

        while current + slot_minutes <= end:
            slot_start = minutes_to_time(current)
            slot_end = minutes_to_time(current + slot_minutes)

            slots.append({
                "start": slot_start,
                "end": slot_end
            })

            current += slot_minutes

    return slots

def get_booked_slots(clinical_data, doctor_id, date):
    booked_slots = []

    for appointment in clinical_data["appointments"]:
        if(
            appointment["doctor_id"] == doctor_id
            and appointment["date"] == date
            and appointment["status"] == "booked"
        ):
            booked_slots.append({
                "start": appointment["start"],
                "end": appointment["end"]
            })

    return booked_slots     

def remove_booked_slots(slots, booked_slots):
    available_slots = []

    for slot in slots:

        slot_start = time_to_minutes(slot["start"])
        slot_end = time_to_minutes(slot["end"])

        is_booked = False

        for booked in booked_slots:

            booked_start = time_to_minutes(booked["start"])
            booked_end = time_to_minutes(booked["end"])


            if(
                slot_start < booked_end
                and slot_end > booked_start
            ):
                is_booked = True
                break

        if not is_booked:
            available_slots.append(slot)

    return available_slots

def search_slots(clinic_data, doctor_id, date):

    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return {
            "status": "error",
            "error": "Invalid date format. Expected YYYY-MM-DD."
        }

    doctor = find_doctor(clinic_data, doctor_id)

    if doctor is None:
        return {
            "status": "error",
            "error": "Doctor not found"
        }

    if date in clinic_data["holidays"]:
        return {
            "status": "no_slots",
            "reason": "Clinic is closed on this date",
            "slots": []
        }

    day_name = get_day_name(date)

    windows = get_working_windows(doctor, day_name)

    if not windows:
        return {
            "status": "no_slots",
            "reason": "Doctor is not available on this day",
            "slots": []
        }

    slots = generate_slots(
        windows,
        clinic_data["clinic"]["slot_minutes"]
    )

    booked_slots = get_booked_slots(
        clinic_data,
        doctor_id,
        date
    )

    available_slots = remove_booked_slots(
        slots,
        booked_slots
    )

    return{
        "status": "ok",
        "doctor_id": doctor_id,
        "date": date,
        "slots": available_slots
    }