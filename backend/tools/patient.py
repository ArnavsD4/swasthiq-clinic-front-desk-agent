def lookup_patient(patients, name=None, phone=None, dob=None):
    if not name and not phone and not dob:
        return{
            "status": "error",
            "error": "Atleast one of name , phone or dob is required."
        }

    candidates = patients

    if name:
        name = name.strip().lower()
        candidates = [
            patient
            for patient in candidates
            if name in patient["name"].lower()
        ]

    if phone:
        phone = str(phone).strip()    
        candidates = [
            patient
            for patient in candidates
            if patient["phone"] == phone
        ]

    if dob:
        dob = dob.strip()
        candidates = [
            patient
            for patient in candidates
            if patient["dob"] == dob
        ]    

    if len(candidates) == 0:
        return {
            "status": "not found",
            "candidates": []
        }

    if len(candidates) > 1:
        return {
            "status": "ambigous",
            "candidates": candidates
        }

    return {
        "status": "resolved",
        "patient": candidates[0]
    }
           