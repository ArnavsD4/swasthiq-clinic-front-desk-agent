def cancel_appointment(
    clinical_data,
    appointment_id,
    patient_id
):

    # 1. Find appointment
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

    # 2. Check patient ownership
    if appointment["patient_id"] != patient_id:
        return {
            "status": "error",
            "error": "Appointment does not belong to patient"
        }

    # 3. Check appointment status
    if appointment["status"] != "booked":
        return {
            "status": "error",
            "error": "Appointment is already cancelled"
        }

    # 4. Cancel appointment
    appointment["status"] = "cancelled"

    # 5. Return updated appointment
    return {
        "status": "cancelled",
        "appointment": appointment
    }