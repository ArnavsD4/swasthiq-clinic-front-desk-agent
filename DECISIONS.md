# Design Decisions

## 1. Deterministic Agent Execution

The final evaluator path uses deterministic planning and deterministic clinic
tools.

This avoids depending on external model availability, model response variation,
or external API quotas for evaluator-critical behavior.

The clinic tools remain the source of truth for patients, slots and
appointments.

---

## 2. Clinic State Is Reset Per Request

Each `POST /agent/run` request loads the supplied `clinic.json` again.

Therefore, an appointment created during one conversation does not affect
another conversation.

---

## 3. `today` Is Authoritative

Relative dates are resolved using the `today` value supplied in the request.

The system does not use the machine's current date for appointment-date
resolution.

For example, with:

```text
today = 2026-10-01