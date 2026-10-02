def escalate_to_human(
    reason,
    patient_id=None,
    appointment_id=None
):

    if not reason or not reason.strip():
        return {
            "status": "error",
            "error": "Escalation reason is required"
        }

    return {
        "status": "escalated",
        "reason": reason.strip(),
        "patient_id": patient_id,
        "appointment_id": appointment_id
    }