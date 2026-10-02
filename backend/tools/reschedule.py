from datetime import datetime

from tools.slots import (
    find_doctor,
    get_day_name,
    get_working_windows,
    generate_slots,
    get_booked_slots
)


def reschedule_appointment(
    clinical_data,
    appointment_id,
    patient_id,
    new_date,
    new_start,
    new_end
):

    # 1. Find the appointment
    appointment = None

    for a in clinical_data["appointments"]:
        if a["id"] == appointment_id:
            appointment = a
            break

    if appointment is None:
        return {
            "status": "error",
            "error": "Appointment not found"
        }

    # 2. Make sure appointment belongs to this patient
    if appointment["patient_id"] != patient_id:
        return {
            "status": "error",
            "error": "Appointment does not belong to patient"
        }

    # 3. Make sure appointment is still active
    if appointment["status"] != "booked":
        return {
            "status": "error",
            "error": "Appointment is not active"
        }

    # 4. Find the doctor
    doctor = find_doctor(
        clinical_data,
        appointment["doctor_id"]
    )

    if doctor is None:
        return {
            "status": "error",
            "error": "Doctor not found"
        }

    # 5. Validate the new date
    try:
        datetime.strptime(
            new_date,
            "%Y-%m-%d"
        )
    except ValueError:
        return {
            "status": "error",
            "error": "Invalid date format"
        }

    try:
        datetime.strptime(new_start, "%H:%M")
        datetime.strptime(new_end, "%H:%M")
    except ValueError:
        return {
            "status": "error",
            "error": "Invalid time format. Expected HH:MM."
        }

    start_time = datetime.strptime(new_start, "%H:%M")
    end_time = datetime.strptime(new_end, "%H:%M")

    if start_time >= end_time:
        return {
            "status": "error",
            "error": "Start time must be before end time"
        }

    # 6. Check whether clinic is closed
    if new_date in clinical_data["holidays"]:
        return {
            "status": "no_slots",
            "reason": "Clinic is closed on this date"
        }

    # 7. Check doctor's working day
    day_name = get_day_name(new_date)

    windows = get_working_windows(
        doctor,
        day_name
    )

    if not windows:
        return {
            "status": "no_slots",
            "reason": "Doctor is not working on this date"
        }

    # 8. Generate valid slots
    slots = generate_slots(
        windows,
        clinical_data["clinic"]["slot_minutes"]
    )

    requested_slot = {
        "start": new_start,
        "end": new_end
    }

    if requested_slot not in slots:
        return {
            "status": "error",
            "error": "Requested slot is not a valid clinic slot"
        }

    # 9. Check whether new slot is already booked
    booked_slots = get_booked_slots(
        clinical_data,
        appointment["doctor_id"],
        new_date
    )

    for booked in booked_slots:

        # Ignore the appointment we are currently rescheduling
        if (
            appointment["date"] == new_date
            and appointment["start"] == booked["start"]
            and appointment["end"] == booked["end"]
        ):
            continue

        if (
            new_start < booked["end"]
            and new_end > booked["start"]
        ):
            return {
                "status": "error",
                "error": "Requested slot is already booked"
            }

    # 10. Update appointment
    appointment["date"] = new_date
    appointment["start"] = new_start
    appointment["end"] = new_end

    # 11. Return updated appointment
    return {
        "status": "rescheduled",
        "appointment": appointment
    }