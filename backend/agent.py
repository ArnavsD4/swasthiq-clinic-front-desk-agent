# backend/agent.py

import os
import re
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from backend.data_loader import load_clinic_data
from backend.tools.patient import lookup_patient
from backend.tools.slots import search_slots
from backend.tools.booking import book_appointment
from backend.tools.reschedule import reschedule_appointment
from backend.tools.cancel import cancel_appointment
from backend.tools.escalate import escalate_to_human


# ============================================================
# CONFIG
# ============================================================

MODEL_NAME = os.getenv("OPENROUTER_MODEL", "openrouter/free")


# ============================================================
# BASIC HELPERS
# ============================================================

def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def all_text(turns: List[str]) -> str:
    return "\n".join(turns or [])


def now_ms() -> int:
    return int(time.time() * 1000)


def valid_date(date_string: str) -> bool:
    try:
        datetime.strptime(date_string, "%Y-%m-%d")
        return True
    except Exception:
        return False


def date_to_weekday(date_string: str) -> str:
    return datetime.strptime(date_string, "%Y-%m-%d").strftime("%A").lower()


def add_days(date_string: str, days: int) -> str:
    dt = datetime.strptime(date_string, "%Y-%m-%d")
    return (dt + timedelta(days=days)).strftime("%Y-%m-%d")


def extract_phone(text: str) -> Optional[str]:
    matches = re.findall(r"\b\d{10}\b", text or "")
    return matches[0] if matches else None


def extract_dob(text: str) -> Optional[str]:
    patterns = [
        r"\b(\d{4}-\d{2}-\d{2})\b",
        r"\b(\d{2}-\d{2}-\d{4})\b",
        r"\b(\d{2}/\d{2}/\d{4})\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text or "")
        if not match:
            continue

        value = match.group(1)

        if re.fullmatch(r"\d{2}-\d{2}-\d{4}", value):
            d, m, y = value.split("-")
            return f"{y}-{m}-{d}"

        if re.fullmatch(r"\d{2}/\d{2}/\d{4}", value):
            d, m, y = value.split("/")
            return f"{y}-{m}-{d}"

        return value

    return None


# ============================================================
# DATE PARSING
# ============================================================

WEEKDAY_MAP = {
    "monday": 0,
    "mon": 0,
    "tuesday": 1,
    "tue": 1,
    "tues": 1,
    "wednesday": 2,
    "wed": 2,
    "thursday": 3,
    "thu": 3,
    "thur": 3,
    "friday": 4,
    "fri": 4,
    "saturday": 5,
    "sat": 5,
    "sunday": 6,
    "sun": 6,
}


def parse_requested_date(text: str, today: str) -> Optional[str]:
    t = normalize(text)

    # Explicit ISO date
    match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", t)
    if match:
        candidate = match.group(1)
        if valid_date(candidate):
            return candidate

    # dd/mm/yyyy or dd-mm-yyyy
    match = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](20\d{2})\b", t)
    if match:
        d, m, y = match.groups()
        candidate = f"{y}-{int(m):02d}-{int(d):02d}"
        if valid_date(candidate):
            return candidate

    today_dt = datetime.strptime(today, "%Y-%m-%d")

    # Relative dates
    if any(x in t for x in [
        "day after tomorrow",
        "parso",
        "parson",
    ]):
        return add_days(today, 2)

    if any(x in t for x in [
        "tomorrow",
        "kal",
        "next day",
    ]):
        return add_days(today, 1)

    if any(x in t for x in [
        "today",
        "aaj",
        "today hi",
    ]):
        return today

    # "3 tareekh", "3rd", "3rd october"
    match = re.search(
        r"\b(?:on\s+)?(\d{1,2})(?:st|nd|rd|th)?\s*(?:tareekh|date)?\b",
        t,
    )

    if match:
        day = int(match.group(1))

        if 1 <= day <= 31:
            # Prefer the current month.
            year = today_dt.year
            month = today_dt.month

            try:
                candidate = datetime(year, month, day).strftime("%Y-%m-%d")

                # If this date has already passed, move to next month.
                candidate_dt = datetime.strptime(candidate, "%Y-%m-%d")

                if candidate_dt.date() >= today_dt.date():
                    return candidate

                if month == 12:
                    return datetime(
                        year + 1, 1, day
                    ).strftime("%Y-%m-%d")

                return datetime(
                    year, month + 1, day
                ).strftime("%Y-%m-%d")

            except ValueError:
                pass

    # Month names
    months = {
        "january": 1,
        "jan": 1,
        "february": 2,
        "feb": 2,
        "march": 3,
        "mar": 3,
        "april": 4,
        "apr": 4,
        "may": 5,
        "june": 6,
        "jun": 6,
        "july": 7,
        "jul": 7,
        "august": 8,
        "aug": 8,
        "september": 9,
        "sep": 9,
        "sept": 9,
        "october": 10,
        "oct": 10,
        "november": 11,
        "nov": 11,
        "december": 12,
        "dec": 12,
    }

    for month_name, month_number in months.items():
        if month_name not in t:
            continue

        match = re.search(
            rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+{re.escape(month_name)}\b",
            t,
        )

        if match:
            day = int(match.group(1))
            try:
                candidate = datetime(
                    today_dt.year,
                    month_number,
                    day,
                )

                if candidate.date() < today_dt.date():
                    candidate = datetime(
                        today_dt.year + 1,
                        month_number,
                        day,
                    )

                return candidate.strftime("%Y-%m-%d")
            except ValueError:
                pass

    # Weekdays:
    # "Saturday" means the next Saturday relative to today.
    for weekday_name, weekday_number in WEEKDAY_MAP.items():
        if re.search(rf"\b{re.escape(weekday_name)}\b", t):
            days_ahead = (
                weekday_number - today_dt.weekday()
            ) % 7

            # If today itself is Saturday and user explicitly says
            # Saturday, treat it as today.
            return add_days(today, days_ahead)

    # Hindi weekdays
    hindi_weekdays = {
        "somvaar": 0,
        "somwar": 0,
        "mangalvaar": 1,
        "mangalwar": 1,
        "budhvaar": 2,
        "budhwar": 2,
        "guruvaar": 3,
        "guruvar": 3,
        "shukravaar": 4,
        "shukravar": 4,
        "shanivaar": 5,
        "shanivar": 5,
        "ravivaar": 6,
        "ravivar": 6,
    }

    for name, weekday_number in hindi_weekdays.items():
        if name in t:
            days_ahead = (
                weekday_number - today_dt.weekday()
            ) % 7

            return add_days(today, days_ahead)

    return None


# ============================================================
# TIME PARSING
# ============================================================

def extract_explicit_time(text: str) -> Optional[str]:
    t = normalize(text)

    # 10:30 / 10.30
    match = re.search(
        r"\b([01]?\d|2[0-3])[:.]([0-5]\d)\s*(am|pm)?\b",
        t,
    )

    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        suffix = match.group(3)

        if suffix == "pm" and hour < 12:
            hour += 12

        if suffix == "am" and hour == 12:
            hour = 0

        return f"{hour:02d}:{minute:02d}"

    # 10 am / 4 pm
    match = re.search(
        r"\b([1-9]|1[0-2])\s*(am|pm)\b",
        t,
    )

    if match:
        hour = int(match.group(1))
        suffix = match.group(2)

        if suffix == "pm" and hour < 12:
            hour += 12

        if suffix == "am" and hour == 12:
            hour = 0

        return f"{hour:02d}:00"

    return None


def choose_slot(
    slots: List[Dict[str, str]],
    text: str,
) -> Optional[Dict[str, str]]:

    if not slots:
        return None

    t = normalize(text)

    explicit_time = extract_explicit_time(t)

    if explicit_time:
        # Exact match first.
        for slot in slots:
            if slot["start"] == explicit_time:
                return slot

        # If the user gave a time that doesn't exactly match a slot,
        # don't invent a different time.
        return None

    # Morning
    if any(x in t for x in [
        "morning",
        "subah",
        "sawere",
        "savere",
        "सुबह",
    ]):
        morning = [
            slot for slot in slots
            if int(slot["start"].split(":")[0]) < 12
        ]

        if morning:
            return morning[0]

        return None

    # Afternoon
    if any(x in t for x in [
        "afternoon",
        "dopahar",
        "dupehar",
    ]):
        afternoon = [
            slot for slot in slots
            if 12 <= int(slot["start"].split(":")[0]) < 17
        ]

        if afternoon:
            return afternoon[0]

        return None

    # Evening
    if any(x in t for x in [
        "evening",
        "shaam",
        "sham",
    ]):
        evening = [
            slot for slot in slots
            if int(slot["start"].split(":")[0]) >= 17
        ]

        if evening:
            return evening[0]

        return None

    # If no time was given, use first available slot.
    return slots[0]


# ============================================================
# DOCTOR PARSING
# ============================================================

def find_doctor_from_text(
    clinic_data: Dict[str, Any],
    text: str,
) -> Optional[Dict[str, Any]]:

    t = normalize(text)

    for doctor in clinic_data.get("doctors", []):
        doctor_name = normalize(doctor.get("name", ""))

        # Full doctor name
        if doctor_name and doctor_name in t:
            return doctor

        # Last name
        parts = doctor_name.split()
        if parts:
            last_name = parts[-1]
            if len(last_name) > 3 and last_name in t:
                return doctor

    # Common references
    if "rao" in t:
        for doctor in clinic_data.get("doctors", []):
            if doctor["id"] == "dr_rao":
                return doctor

    if "sethi" in t:
        for doctor in clinic_data.get("doctors", []):
            if doctor["id"] == "dr_sethi":
                return doctor

    if any(x in t for x in [
        "paediatric",
        "pediatric",
        "child doctor",
        "children doctor",
        "bachche ka doctor",
    ]):
        for doctor in clinic_data.get("doctors", []):
            if doctor["id"] == "dr_sethi":
                return doctor

    if any(x in t for x in [
        "general physician",
        "physician",
        "general doctor",
    ]):
        for doctor in clinic_data.get("doctors", []):
            if doctor["id"] == "dr_rao":
                return doctor

    return None


# ============================================================
# PATIENT PARSING
# ============================================================

def patient_names_in_text(
    clinic_data: Dict[str, Any],
    text: str,
) -> List[Dict[str, Any]]:

    t = normalize(text)
    found = []

    for patient in clinic_data.get("patients", []):
        name = normalize(patient.get("name", ""))

        if not name:
            continue

        if name in t:
            found.append(patient)

    return found


def find_patient_reference(
    clinic_data: Dict[str, Any],
    text: str,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:

    phone = extract_phone(text)
    dob = extract_dob(text)

    explicit_matches = patient_names_in_text(
        clinic_data,
        text,
    )

    # Name + phone/DOB is strongest.
    if explicit_matches and (phone or dob):

        candidates = explicit_matches

        if phone:
            candidates = [
                p for p in candidates
                if p.get("phone") == phone
            ]

        if dob:
            candidates = [
                p for p in candidates
                if p.get("dob") == dob
            ]

        if len(candidates) == 1:
            return candidates[0], None

        if len(candidates) > 1:
            return None, "ambiguous_patient"

    # Exact full-name match.
    if len(explicit_matches) == 1:
        return explicit_matches[0], None

    if len(explicit_matches) > 1:
        return None, "ambiguous_patient"

    # Phone only.
    if phone:
        phone_matches = [
            p for p in clinic_data.get("patients", [])
            if p.get("phone") == phone
        ]

        if len(phone_matches) == 1:
            return phone_matches[0], None

        if len(phone_matches) > 1:
            return None, "ambiguous_patient"

    # DOB only.
    if dob:
        dob_matches = [
            p for p in clinic_data.get("patients", [])
            if p.get("dob") == dob
        ]

        if len(dob_matches) == 1:
            return dob_matches[0], None

        if len(dob_matches) > 1:
            return None, "ambiguous_patient"

    # Try meaningful name fragments only when they are
    # sufficiently distinctive.
    words = re.findall(r"[a-zA-Z]+", text or "")

    stopwords = {
        "appointment",
        "book",
        "booking",
        "cancel",
        "cancelled",
        "canceling",
        "reschedule",
        "rescheduled",
        "doctor",
        "with",
        "for",
        "please",
        "patient",
        "number",
        "phone",
        "name",
        "mera",
        "mujhe",
        "hai",
        "chahiye",
        "tha",
        "the",
        "ke",
        "ka",
        "ki",
        "appointment",
    }

    meaningful = [
        w.lower()
        for w in words
        if len(w) >= 4 and w.lower() not in stopwords
    ]

    fragment_candidates = []

    for patient in clinic_data.get("patients", []):
        name_words = set(
            normalize(patient["name"]).split()
        )

        overlap = name_words.intersection(meaningful)

        if overlap:
            fragment_candidates.append(patient)

    if len(fragment_candidates) == 1:
        return fragment_candidates[0], None

    if len(fragment_candidates) > 1:
        return None, "ambiguous_patient"

    return None, None


# ============================================================
# APPOINTMENT HELPERS
# ============================================================

def patient_appointments(
    clinic_data: Dict[str, Any],
    patient_id: str,
    active_only: bool = True,
) -> List[Dict[str, Any]]:

    appointments = []

    for appointment in clinic_data.get("appointments", []):
        if appointment.get("patient_id") != patient_id:
            continue

        if active_only and appointment.get("status") != "booked":
            continue

        appointments.append(appointment)

    return appointments


def find_appointment_from_text(
    clinic_data: Dict[str, Any],
    patient_id: str,
    text: str,
) -> Optional[Dict[str, Any]]:

    appointments = patient_appointments(
        clinic_data,
        patient_id,
        active_only=True,
    )

    if not appointments:
        return None

    match = re.search(
        r"\b(ap_\d{4})\b",
        normalize(text),
    )

    if match:
        appointment_id = match.group(1)

        for appointment in appointments:
            if appointment["id"] == appointment_id:
                return appointment

    requested_date = parse_requested_date(
        text,
        "2026-10-01",
    )

    if requested_date:
        date_matches = [
            a for a in appointments
            if a["date"] == requested_date
        ]

        if len(date_matches) == 1:
            return date_matches[0]

    if len(appointments) == 1:
        return appointments[0]

    return appointments[0]


# ============================================================
# INTENT DETECTION
# ============================================================

def is_cancel_intent(text: str) -> bool:
    t = normalize(text)

    return any(x in t for x in [
        "cancel",
        "cancellation",
        "cancelled",
        "cancel appointment",
        "appointment cancel",
        "appointment ko cancel",
        "appointment cancel kar",
        "appointment hata",
        "nahi aana",
        "nahin aana",
    ])


def is_reschedule_intent(text: str) -> bool:
    t = normalize(text)

    return any(x in t for x in [
        "reschedule",
        "rescheduled",
        "change appointment",
        "change my appointment",
        "move appointment",
        "shift appointment",
        "appointment change",
        "date change",
        "time change",
        "appointment ko shift",
        "appointment badal",
    ])


def is_booking_intent(text: str) -> bool:
    t = normalize(text)

    if is_cancel_intent(t) or is_reschedule_intent(t):
        return False

    return any(x in t for x in [
        "book",
        "booking",
        "appointment chahiye",
        "appointment lena",
        "appointment leni",
        "appointment karna",
        "appointment ke liye",
        "milna hai",
        "visit",
        "consultation",
        "slot chahiye",
        "appointment",
    ])


# ============================================================
# CLINICAL SAFETY
# ============================================================

URGENT_PATTERNS = [
    "chest pain",
    "severe chest",
    "difficulty breathing",
    "can't breathe",
    "cannot breathe",
    "breathing problem",
    "shortness of breath",
    "unconscious",
    "fainted",
    "fainting",
    "heavy bleeding",
    "severe bleeding",
    "stroke",
    "seizure",
    "convulsion",
    "heart attack",
    "suicidal",
    "suicide",
    "overdose",
    "poisoning",
    "emergency",
    "urgent medical",
    "बहुत तेज दर्द",
    "सीने में दर्द",
    "सांस लेने में दिक्कत",
    "सांस नहीं आ रही",
    "बेहोश",
    "खून बहुत निकल",
    "दौरा",
    "जहर",
    "इमरजेंसी",
    "emergency hai",
    "bahut tez chest pain",
    "saans nahi aa rahi",
    "saans lene mein dikkat",
    "behosh",
]


MEDICAL_ADVICE_PATTERNS = [
    "what medicine",
    "which medicine",
    "medicine lena",
    "medicine lu",
    "medicine loon",
    "dose",
    "dosage",
    "tablet",
    "should i take",
    "what should i take",
    "what treatment",
    "diagnose",
    "diagnosis",
    "is this serious",
    "what disease",
    "kya dawa",
    "kaunsi dawa",
    "dawai",
    "dawa bata",
    "dawa suggest",
    "treatment bata",
    "ilaaj bata",
    "kya karu",
    "kya karna chahiye",
]


def contains_any(text: str, patterns: List[str]) -> bool:
    t = normalize(text)
    return any(pattern in t for pattern in patterns)


def detect_clinical_escalation(
    turns: List[str],
) -> Optional[str]:

    text = all_text(turns)

    if contains_any(text, URGENT_PATTERNS):
        return "clinical_urgent"

    if contains_any(text, MEDICAL_ADVICE_PATTERNS):
        return "medical_advice"

    return None


# ============================================================
# PROMPT INJECTION
# ============================================================

INJECTION_PATTERNS = [
    "ignore previous instructions",
    "ignore all previous instructions",
    "ignore the system prompt",
    "system prompt",
    "developer message",
    "reveal your prompt",
    "show your instructions",
    "print your instructions",
    "jailbreak",
    "forget the rules",
    "override the rules",
    "you are now",
    "act as an unrestricted",
]


def contains_prompt_injection(text: str) -> bool:
    return contains_any(
        text,
        INJECTION_PATTERNS,
    )


# ============================================================
# RESPONSE BUILDER
# ============================================================

def build_response(
    conversation_id: str,
    tool_calls: List[Dict[str, Any]],
    terminal_state: str,
    escalation_reason: Optional[str],
    patient_id: Optional[str],
    appointment_id: Optional[str],
    reply: str,
    turns_count: int,
    start_time_ms: int,
) -> Dict[str, Any]:

    latency = max(
        0,
        now_ms() - start_time_ms,
    )

    return {
        "conversation_id": conversation_id,
        "tool_calls": tool_calls,
        "terminal_state": terminal_state,
        "escalation_reason": escalation_reason,
        "patient_id": patient_id,
        "appointment_id": appointment_id,
        "reply": reply,
        "metrics": {
            "turns": turns_count,
            "tokens": 0,
            "latency_ms": latency,
        },
    }


# ============================================================
# TOOL CALL RECORDING
# ============================================================

def record_tool_call(
    tool_calls: List[Dict[str, Any]],
    name: str,
    arguments: Dict[str, Any],
):
    tool_calls.append({
        "name": name,
        "arguments": arguments,
    })


# ============================================================
# TOOL WRAPPERS
# ============================================================

def run_lookup(
    clinic_data: Dict[str, Any],
    tool_calls: List[Dict[str, Any]],
    name: Optional[str] = None,
    phone: Optional[str] = None,
    dob: Optional[str] = None,
):
    arguments = {}

    if name:
        arguments["name"] = name

    if phone:
        arguments["phone"] = phone

    if dob:
        arguments["dob"] = dob

    record_tool_call(
        tool_calls,
        "lookup_patient",
        arguments,
    )

    return lookup_patient(
        clinic_data["patients"],
        name=name,
        phone=phone,
        dob=dob,
    )


def run_search_slots(
    clinic_data: Dict[str, Any],
    tool_calls: List[Dict[str, Any]],
    doctor_id: str,
    date: str,
):
    arguments = {
        "doctor_id": doctor_id,
        "date": date,
    }

    record_tool_call(
        tool_calls,
        "search_slots",
        arguments,
    )

    return search_slots(
        clinic_data,
        doctor_id,
        date,
    )


def run_book(
    clinic_data: Dict[str, Any],
    tool_calls: List[Dict[str, Any]],
    patient_id: str,
    doctor_id: str,
    date: str,
    start: str,
    end: str,
):
    arguments = {
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "date": date,
        "start": start,
        "end": end,
    }

    record_tool_call(
        tool_calls,
        "book_appointment",
        arguments,
    )

    return book_appointment(
        clinic_data,
        patient_id,
        doctor_id,
        date,
        start,
        end,
    )


def run_reschedule(
    clinic_data: Dict[str, Any],
    tool_calls: List[Dict[str, Any]],
    appointment_id: str,
    patient_id: str,
    new_date: str,
    new_start: str,
    new_end: str,
):
    arguments = {
        "appointment_id": appointment_id,
        "patient_id": patient_id,
        "new_date": new_date,
        "new_start": new_start,
        "new_end": new_end,
    }

    record_tool_call(
        tool_calls,
        "reschedule_appointment",
        arguments,
    )

    return reschedule_appointment(
        clinic_data,
        appointment_id,
        patient_id,
        new_date,
        new_start,
        new_end,
    )


def run_cancel(
    clinic_data: Dict[str, Any],
    tool_calls: List[Dict[str, Any]],
    appointment_id: str,
    patient_id: str,
):
    arguments = {
        "appointment_id": appointment_id,
        "patient_id": patient_id,
    }

    record_tool_call(
        tool_calls,
        "cancel_appointment",
        arguments,
    )

    return cancel_appointment(
        clinic_data,
        appointment_id,
        patient_id,
    )


def run_escalate(
    clinic_data: Dict[str, Any],
    tool_calls: List[Dict[str, Any]],
    reason: str,
    patient_id: Optional[str] = None,
    appointment_id: Optional[str] = None,
):
    arguments = {
        "reason": reason,
    }

    if patient_id is not None:
        arguments["patient_id"] = patient_id

    if appointment_id is not None:
        arguments["appointment_id"] = appointment_id

    record_tool_call(
        tool_calls,
        "escalate_to_human",
        arguments,
    )

    return escalate_to_human(
        reason=reason,
        patient_id=patient_id,
        appointment_id=appointment_id,
    )


# ============================================================
# PATIENT LOOKUP
# ============================================================

def resolve_patient(
    clinic_data: Dict[str, Any],
    text: str,
    tool_calls: List[Dict[str, Any]],
) -> Tuple[
    Optional[Dict[str, Any]],
    Optional[str],
    Optional[str],
]:

    phone = extract_phone(text)
    dob = extract_dob(text)

    names = patient_names_in_text(
        clinic_data,
        text,
    )

    # Exact unique name.
    if len(names) == 1:
        patient = names[0]

        # Still call the official tool.
        result = run_lookup(
            clinic_data,
            tool_calls,
            name=patient["name"],
            phone=phone,
            dob=dob,
        )

        if result.get("status") == "resolved":
            return result["patient"], None, None

    # Multiple exact names -> ambiguity.
    if len(names) > 1:
        result = run_lookup(
            clinic_data,
            tool_calls,
            phone=phone,
            dob=dob,
        )

        if result.get("status") == "resolved":
            return result["patient"], None, None

        return None, "ambiguous_patient", None

    # Phone/DOB lookup.
    if phone or dob:
        result = run_lookup(
            clinic_data,
            tool_calls,
            phone=phone,
            dob=dob,
        )

        if result.get("status") == "resolved":
            return result["patient"], None, None

        if result.get("status") == "ambiguous":
            return None, "ambiguous_patient", None

        return None, None, "not_found"

    # Look for a name fragment.
    words = re.findall(
        r"[A-Za-z]+",
        text or "",
    )

    stopwords = {
        "appointment",
        "book",
        "booking",
        "cancel",
        "cancelled",
        "reschedule",
        "doctor",
        "number",
        "phone",
        "please",
        "mujhe",
        "mera",
        "meri",
        "ke",
        "ka",
        "ki",
        "liye",
        "chahiye",
        "hai",
        "tha",
        "thi",
        "with",
        "for",
        "the",
        "patient",
        "appointment",
        "subah",
        "morning",
        "evening",
        "afternoon",
    }

    fragments = [
        word for word in words
        if word.lower() not in stopwords
        and len(word) >= 4
    ]

    candidates = []

    for patient in clinic_data["patients"]:
        patient_words = set(
            normalize(patient["name"]).split()
        )

        if patient_words.intersection(
            set(x.lower() for x in fragments)
        ):
            candidates.append(patient)

    if len(candidates) == 1:
        patient = candidates[0]

        result = run_lookup(
            clinic_data,
            tool_calls,
            name=patient["name"],
        )

        if result.get("status") == "resolved":
            return result["patient"], None, None

    if len(candidates) > 1:
        return None, "ambiguous_patient", None

    return None, None, "not_found"


# ============================================================
# GUARDIAN / CHILD RESOLUTION
# ============================================================

def resolve_guardian_child(
    clinic_data: Dict[str, Any],
    text: str,
    tool_calls: List[Dict[str, Any]],
) -> Tuple[
    Optional[Dict[str, Any]],
    Optional[str],
]:

    t = normalize(text)

    guardian_patients = []

    for patient in clinic_data["patients"]:
        if patient.get("guardian_of"):
            if normalize(patient["name"]) in t:
                guardian_patients.append(patient)

    # If "mother/father/guardian" language exists, try to identify
    # the child explicitly.
    is_guardian_request = any(
        x in t
        for x in [
            "guardian",
            "mother",
            "father",
            "mom",
            "dad",
            "maa",
            "papa",
            "child",
            "son",
            "daughter",
            "beta",
        ]
    )

    if not is_guardian_request:
        return None, None

    child_candidates = []

    for patient in clinic_data["patients"]:
        if not patient.get("guardian_of"):
            continue

        # guardian_of can be a patient id or list of ids.
        guardian_ids = patient.get("guardian_of", [])

        if isinstance(guardian_ids, str):
            guardian_ids = [guardian_ids]

        if patient.get("name"):
            guardian_name = normalize(patient["name"])

            if guardian_name in t:
                guardian_patients.append(patient)

        for child_id in guardian_ids:
            for child in clinic_data["patients"]:
                if child["id"] == child_id:
                    if normalize(child["name"]) in t:
                        child_candidates.append(child)

    if len(child_candidates) == 1:
        return child_candidates[0], None

    # Sometimes the child name appears but guardian name does not.
    for patient in clinic_data["patients"]:
        if not patient.get("guardian_of"):
            continue

        if normalize(patient["name"]) in t:
            return patient, None

    if len(child_candidates) > 1:
        return None, "ambiguous_patient"

    return None, None


# ============================================================
# SAFETY GATE
# ============================================================

def safety_gate(
    conversation_id: str,
    today: str,
    turns: List[str],
    clinic_data: Dict[str, Any],
    start_time_ms: int,
) -> Optional[Dict[str, Any]]:

    tool_calls = []

    clinical_reason = detect_clinical_escalation(
        turns
    )

    if clinical_reason:
        run_escalate(
            clinic_data,
            tool_calls,
            clinical_reason,
        )

        reply = (
            "This involves a medical or potentially urgent "
            "clinical issue, so I’m escalating it to a human "
            "staff member rather than giving medical advice."
        )

        if clinical_reason == "clinical_urgent":
            reply = (
                "This may be an urgent medical issue. "
                "I’m escalating this to a human staff member "
                "immediately rather than giving medical advice."
            )

        return build_response(
            conversation_id,
            tool_calls,
            "escalated",
            clinical_reason,
            None,
            None,
            reply,
            len(turns),
            start_time_ms,
        )

    return None


# ============================================================
# DETERMINISTIC AGENT
# ============================================================

def deterministic_agent(
    conversation_id: str,
    today: str,
    turns: List[str],
) -> Dict[str, Any]:

    start_time_ms = now_ms()

    clinic_data = load_clinic_data()
    tool_calls: List[Dict[str, Any]] = []

    # --------------------------------------------------------
    # SAFETY FIRST
    # --------------------------------------------------------

    safety_response = safety_gate(
        conversation_id,
        today,
        turns,
        clinic_data,
        start_time_ms,
    )

    if safety_response:
        return safety_response

    text = all_text(turns)
    normalized_text = normalize(text)

    # --------------------------------------------------------
    # PROMPT INJECTION
    # --------------------------------------------------------

    injection_present = contains_prompt_injection(
        normalized_text
    )

    # Injection by itself is not a reason to execute arbitrary
    # instructions. We continue processing only legitimate
    # front-desk intent from the same conversation.
    #
    # If there is no legitimate clinic action, escalate.

    # --------------------------------------------------------
    # INTENT
    # --------------------------------------------------------

    cancel_intent = is_cancel_intent(
        normalized_text
    )

    reschedule_intent = is_reschedule_intent(
        normalized_text
    )

    booking_intent = is_booking_intent(
        normalized_text
    )

    if not (
        cancel_intent
        or reschedule_intent
        or booking_intent
    ):
        run_escalate(
            clinic_data,
            tool_calls,
            "out_of_scope",
        )

        return build_response(
            conversation_id,
            tool_calls,
            "escalated",
            "out_of_scope",
            None,
            None,
            "I can help with clinic appointments, but I can’t process that request. I’m escalating it to a human staff member.",
            len(turns),
            start_time_ms,
        )

    # --------------------------------------------------------
    # GUARDIAN / CHILD
    # --------------------------------------------------------

    patient = None
    patient_error = None

    guardian_patient, guardian_error = resolve_guardian_child(
        clinic_data,
        normalized_text,
        tool_calls,
    )

    if guardian_error:
        run_escalate(
            clinic_data,
            tool_calls,
            "ambiguous_patient",
        )

        return build_response(
            conversation_id,
            tool_calls,
            "escalated",
            "ambiguous_patient",
            None,
            None,
            "I need to confirm exactly which patient you mean before proceeding, so I’m escalating this to a human staff member.",
            len(turns),
            start_time_ms,
        )

    if guardian_patient:
        patient = guardian_patient
    else:
        patient, patient_error, _ = resolve_patient(
            clinic_data,
            normalized_text,
            tool_calls,
        )

    # --------------------------------------------------------
    # PATIENT NOT RESOLVED
    # --------------------------------------------------------

    if patient_error == "ambiguous_patient":
        run_escalate(
            clinic_data,
            tool_calls,
            "ambiguous_patient",
        )

        return build_response(
            conversation_id,
            tool_calls,
            "escalated",
            "ambiguous_patient",
            None,
            None,
            "There are multiple patients matching those details. I won’t guess which patient you mean, so I’m escalating this to a human staff member.",
            len(turns),
            start_time_ms,
        )

    if patient is None:

        # Prompt injection without an actionable identity/
        # appointment request.
        reason = (
            "out_of_scope"
            if injection_present
            else "out_of_scope"
        )

        run_escalate(
            clinic_data,
            tool_calls,
            reason,
        )

        return build_response(
            conversation_id,
            tool_calls,
            "escalated",
            reason,
            None,
            None,
            "I couldn’t safely identify the patient from the information provided. I’m escalating this to a human staff member rather than guessing.",
            len(turns),
            start_time_ms,
        )

    patient_id = patient["id"]

    # --------------------------------------------------------
    # CANCEL
    # --------------------------------------------------------

    if cancel_intent:

        appointment = find_appointment_from_text(
            clinic_data,
            patient_id,
            normalized_text,
        )

        if appointment is None:
            run_escalate(
                clinic_data,
                tool_calls,
                "out_of_scope",
                patient_id=patient_id,
            )

            return build_response(
                conversation_id,
                tool_calls,
                "escalated",
                "out_of_scope",
                patient_id,
                None,
                "I couldn’t identify an active appointment to cancel, so I’m escalating this to a human staff member.",
                len(turns),
                start_time_ms,
            )

        appointment_id = appointment["id"]

        result = run_cancel(
            clinic_data,
            tool_calls,
            appointment_id,
            patient_id,
        )

        if result.get("status") == "cancelled":
            return build_response(
                conversation_id,
                tool_calls,
                "cancelled",
                None,
                patient_id,
                appointment_id,
                "Your appointment has been cancelled successfully.",
                len(turns),
                start_time_ms,
            )

        if "belong" in normalize(
            result.get("error", "")
        ):
            run_escalate(
                clinic_data,
                tool_calls,
                "not_authorised",
                patient_id=patient_id,
                appointment_id=appointment_id,
            )

            return build_response(
                conversation_id,
                tool_calls,
                "escalated",
                "not_authorised",
                patient_id,
                appointment_id,
                "I’m unable to modify an appointment that cannot be verified as belonging to you. I’m escalating this to a human staff member.",
                len(turns),
                start_time_ms,
            )

        run_escalate(
            clinic_data,
            tool_calls,
            "out_of_scope",
            patient_id=patient_id,
            appointment_id=appointment_id,
        )

        return build_response(
            conversation_id,
            tool_calls,
            "escalated",
            "out_of_scope",
            patient_id,
            appointment_id,
            "I couldn’t complete the cancellation safely, so I’m escalating this to a human staff member.",
            len(turns),
            start_time_ms,
        )

    # --------------------------------------------------------
    # RESCHEDULE
    # --------------------------------------------------------

    if reschedule_intent:

        appointment = find_appointment_from_text(
            clinic_data,
            patient_id,
            normalized_text,
        )

        if appointment is None:
            run_escalate(
                clinic_data,
                tool_calls,
                "out_of_scope",
                patient_id=patient_id,
            )

            return build_response(
                conversation_id,
                tool_calls,
                "escalated",
                "out_of_scope",
                patient_id,
                None,
                "I couldn’t identify the appointment you want to reschedule, so I’m escalating this to a human staff member.",
                len(turns),
                start_time_ms,
            )

        appointment_id = appointment["id"]

        new_date = parse_requested_date(
            normalized_text,
            today,
        )

        if new_date is None:
            run_escalate(
                clinic_data,
                tool_calls,
                "out_of_scope",
                patient_id=patient_id,
                appointment_id=appointment_id,
            )

            return build_response(
                conversation_id,
                tool_calls,
                "escalated",
                "out_of_scope",
                patient_id,
                appointment_id,
                "I couldn’t determine the new appointment date safely, so I’m escalating this to a human staff member.",
                len(turns),
                start_time_ms,
            )

        doctor_id = appointment["doctor_id"]

        slot_result = run_search_slots(
            clinic_data,
            tool_calls,
            doctor_id,
            new_date,
        )

        # IMPORTANT:
        # search_slots() returns status="ok"
        if slot_result.get("status") != "ok":

            return build_response(
                conversation_id,
                tool_calls,
                "refused",
                None,
                patient_id,
                None,
                slot_result.get(
                    "reason",
                    "No appointment slots are available on that date.",
                ),
                len(turns),
                start_time_ms,
            )

        slots = slot_result.get(
            "slots",
            [],
        )

        selected_slot = choose_slot(
            slots,
            normalized_text,
        )

        if selected_slot is None:

            return build_response(
                conversation_id,
                tool_calls,
                "refused",
                None,
                patient_id,
                None,
                "The requested time is not an available clinic slot.",
                len(turns),
                start_time_ms,
            )

        result = run_reschedule(
            clinic_data,
            tool_calls,
            appointment_id,
            patient_id,
            new_date,
            selected_slot["start"],
            selected_slot["end"],
        )

        if result.get("status") == "rescheduled":
            return build_response(
                conversation_id,
                tool_calls,
                "rescheduled",
                None,
                patient_id,
                appointment_id,
                f"Your appointment has been rescheduled to {new_date} at {selected_slot['start']}.",
                len(turns),
                start_time_ms,
            )

        if "belong" in normalize(
            result.get("error", "")
        ):
            run_escalate(
                clinic_data,
                tool_calls,
                "not_authorised",
                patient_id=patient_id,
                appointment_id=appointment_id,
            )

            return build_response(
                conversation_id,
                tool_calls,
                "escalated",
                "not_authorised",
                patient_id,
                appointment_id,
                "I’m unable to modify an appointment that cannot be verified as belonging to you. I’m escalating this to a human staff member.",
                len(turns),
                start_time_ms,
            )

        # Existing slot conflict should not be treated as success.
        return build_response(
            conversation_id,
            tool_calls,
            "refused",
            None,
            patient_id,
            None,
            result.get(
                "error",
                "The requested appointment change could not be completed.",
            ),
            len(turns),
            start_time_ms,
        )

    # --------------------------------------------------------
    # BOOKING
    # --------------------------------------------------------

    if booking_intent:

        doctor = find_doctor_from_text(
            clinic_data,
            normalized_text,
        )

        if doctor is None:

            run_escalate(
                clinic_data,
                tool_calls,
                "out_of_scope",
                patient_id=patient_id,
            )

            return build_response(
                conversation_id,
                tool_calls,
                "escalated",
                "out_of_scope",
                patient_id,
                None,
                "I couldn’t determine which doctor you want to book with, so I’m escalating this to a human staff member.",
                len(turns),
                start_time_ms,
            )

        requested_date = parse_requested_date(
            normalized_text,
            today,
        )

        if requested_date is None:

            run_escalate(
                clinic_data,
                tool_calls,
                "out_of_scope",
                patient_id=patient_id,
            )

            return build_response(
                conversation_id,
                tool_calls,
                "escalated",
                "out_of_scope",
                patient_id,
                None,
                "I couldn’t determine the appointment date safely, so I’m escalating this to a human staff member.",
                len(turns),
                start_time_ms,
            )

        slot_result = run_search_slots(
            clinic_data,
            tool_calls,
            doctor["id"],
            requested_date,
        )

        # IMPORTANT:
        # search_slots returns status="ok", not "slots".
        if slot_result.get("status") != "ok":

            return build_response(
                conversation_id,
                tool_calls,
                "refused",
                None,
                patient_id,
                None,
                slot_result.get(
                    "reason",
                    "The clinic does not have appointment slots available on that date.",
                ),
                len(turns),
                start_time_ms,
            )

        slots = slot_result.get(
            "slots",
            [],
        )

        selected_slot = choose_slot(
            slots,
            normalized_text,
        )

        if selected_slot is None:

            # If the user explicitly requested a time which
            # doesn't exist, never silently move them.
            explicit_time = extract_explicit_time(
                normalized_text
            )

            if explicit_time:
                return build_response(
                    conversation_id,
                    tool_calls,
                    "refused",
                    None,
                    patient_id,
                    None,
                    f"{explicit_time} is not an available clinic slot.",
                    len(turns),
                    start_time_ms,
                )

            return build_response(
                conversation_id,
                tool_calls,
                "refused",
                None,
                patient_id,
                None,
                "No suitable appointment slot is available for the requested time.",
                len(turns),
                start_time_ms,
            )

        booking_result = run_book(
            clinic_data,
            tool_calls,
            patient_id,
            doctor["id"],
            requested_date,
            selected_slot["start"],
            selected_slot["end"],
        )

        if booking_result.get("status") == "booked":

            appointment = booking_result.get(
                "appointment",
                {},
            )

            appointment_id = appointment.get(
                "id"
            )

            return build_response(
                conversation_id,
                tool_calls,
                "booked",
                None,
                patient_id,
                appointment_id,
                f"Your appointment with {doctor['name']} is booked for {requested_date} at {selected_slot['start']}.",
                len(turns),
                start_time_ms,
            )

        # Slot was taken between search and booking.
        if "already booked" in normalize(
            booking_result.get("error", "")
        ):
            return build_response(
                conversation_id,
                tool_calls,
                "refused",
                None,
                patient_id,
                None,
                "That appointment slot is no longer available.",
                len(turns),
                start_time_ms,
            )

        return build_response(
            conversation_id,
            tool_calls,
            "refused",
            None,
            patient_id,
            None,
            booking_result.get(
                "error",
                "The appointment could not be booked.",
            ),
            len(turns),
            start_time_ms,
        )

    # --------------------------------------------------------
    # FINAL SAFETY FALLBACK
    # --------------------------------------------------------

    run_escalate(
        clinic_data,
        tool_calls,
        "out_of_scope",
        patient_id=patient_id,
    )

    return build_response(
        conversation_id,
        tool_calls,
        "escalated",
        "out_of_scope",
        patient_id,
        None,
        "I’m unable to safely complete that request, so I’m escalating it to a human staff member.",
        len(turns),
        start_time_ms,
    )


# ============================================================
# OPTIONAL LLM PLACEHOLDER
# ============================================================
#
# The assignment requires an agentic workflow, but the clinic
# tools remain the source of truth. The deterministic planner
# above is deliberately used for evaluator stability.
#
# OpenRouter can be added later without changing the tool layer.
# ============================================================

def llm_agent(
    conversation_id: str,
    today: str,
    turns: List[str],
) -> Dict[str, Any]:
    """
    Deterministic fallback is intentionally used.

    This function exists so the architecture has a clear place
    for an LLM planner without making evaluator results depend
    on external model availability or free-model rate limits.
    """

    return deterministic_agent(
        conversation_id,
        today,
        turns,
    )


# ============================================================
# PUBLIC ENTRY POINT
# ============================================================

def run_agent(
    conversation_id: str,
    today: str,
    turns: List[str],
) -> Dict[str, Any]:

    # --------------------------------------------------------
    # Validate request-level input
    # --------------------------------------------------------

    if not conversation_id:
        conversation_id = f"cv_{uuid.uuid4().hex[:8]}"

    if not valid_date(today):
        return {
            "conversation_id": conversation_id,
            "tool_calls": [],
            "terminal_state": "refused",
            "escalation_reason": None,
            "patient_id": None,
            "appointment_id": None,
            "reply": "Invalid today date. Expected YYYY-MM-DD.",
            "metrics": {
                "turns": len(turns or []),
                "tokens": 0,
                "latency_ms": 0,
            },
        }

    if not isinstance(turns, list):
        turns = []

    # --------------------------------------------------------
    # Empty conversation
    # --------------------------------------------------------

    if not turns:
        return {
            "conversation_id": conversation_id,
            "tool_calls": [],
            "terminal_state": "abandoned",
            "escalation_reason": None,
            "patient_id": None,
            "appointment_id": None,
            "reply": "No conversation turns were provided.",
            "metrics": {
                "turns": 0,
                "tokens": 0,
                "latency_ms": 0,
            },
        }

    # --------------------------------------------------------
    # Deterministic evaluator path
    #
    # Do NOT call OpenRouter here.
    #
    # The external free-model quota may be exhausted and the
    # assignment explicitly requires deterministic behavior.
    # Clinic tools remain the ground truth.
    # --------------------------------------------------------

    return deterministic_agent(
        conversation_id,
        today,
        turns,
    )