from datetime import datetime
from threading import Lock

from tools.slots import(
    find_doctor,
    get_day_name,
    get_working_windows,
    generate_slots,
    get_booked_slots
)

booking_lock = Lock()

def book_appointment(
        clinical_data,
        patient_id,
        doctor_id,
        date,
        start,
        end
):

    patient = None

    for p in clinical_data["patients"]:
        if p["id"] == patient_id:
            patient = p
            break

    if patient is None:
        return {
            "status": "error",
            "error": "Patient not found"
        }

    doctor = find_doctor(clinical_data, doctor_id)

    if doctor is None:
        return {
            "status": "error",
            "error": "Doctor not found"
        }

    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return {
            "status": "error",
            "error": "Invalid date format"
        }

    try:
        datetime.strptime(start, "%H:%M")
        datetime.strptime(end, "%H:%M")
    except ValueError:
        return {
            "status": "error",
            "error": "Invalid time format. Expected HH:MM."
        }

    start_time = datetime.strptime(start, "%H:%M")
    end_time = datetime.strptime(end, "%H:%M")

    if start_time >= end_time:
        return {
            "status": "error",
            "error": "Start time must be before end time"
        }

    if date in clinical_data["holidays"]:
        return{
            "status": "no_slots",
            "reason": "Clinic is closed on this date"
        }

    day_name = get_day_name(date)

    windows = get_working_windows(
        doctor,
        day_name
    )

    if not windows:
        return{
            "status": "no_slots",
            "reason": "Doctor is not working on this date"
        }

    slots = generate_slots(
        windows,
        clinical_data["clinic"]["slot_minutes"]
    )

    requested_slot = {
        "start": start,
        "end": end
    }

    if requested_slot not in slots:
        return {
            "status": "error",
            "error": "Requested slot is not a valid clinic slot"
        }

    with booking_lock:

        booked_slots = get_booked_slots(
        clinical_data,
        doctor_id,
        date
    )

    for booked in booked_slots:
        if (
            start < booked["end"]
            and end > booked["start"]
        ):
            return {
                "status": "error",
                "error": "Requested slot is already booked"
            }

    appointment_id = (
        f"ap_{len(clinical_data['appointments']) + 1:04d}"
    )

    appointment = {
        "id": appointment_id,
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "date": date,
        "start": start,
        "end": end,
        "status": "booked"
    }

    clinical_data["appointments"].append(appointment)

    return {
        "status": "booked",
        "appointment": appointment
    }



    