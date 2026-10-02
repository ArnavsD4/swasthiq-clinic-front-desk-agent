from tools.escalate import escalate_to_human


# --------------------------------------------------
# TEST 1: Basic escalation
# --------------------------------------------------

result = escalate_to_human(
    "Patient identity is ambiguous"
)

print("\nTEST 1 - Basic escalation")
print(result)


# --------------------------------------------------
# TEST 2: Escalation with patient ID
# --------------------------------------------------

result = escalate_to_human(
    "Caller is not authorized",
    patient_id="pt_0001"
)

print("\nTEST 2 - With patient ID")
print(result)


# --------------------------------------------------
# TEST 3: Escalation with appointment ID
# --------------------------------------------------

result = escalate_to_human(
    "Caller is not authorized to modify appointment",
    patient_id="pt_0001",
    appointment_id="ap_0001"
)

print("\nTEST 3 - With appointment ID")
print(result)


# --------------------------------------------------
# TEST 4: Missing reason
# --------------------------------------------------

result = escalate_to_human(
    ""
)

print("\nTEST 4 - Missing reason")
print(result)


# --------------------------------------------------
# TEST 5: Whitespace reason
# --------------------------------------------------

result = escalate_to_human(
    "     "
)

print("\nTEST 5 - Whitespace reason")
print(result)