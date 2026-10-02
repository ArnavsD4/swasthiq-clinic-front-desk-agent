# SwasthiQ — Clinic Front Desk Agent

A deterministic, tool-using AI-style clinic front desk agent for Sunrise Clinic, Dehradun.

The system handles appointment booking, rescheduling, cancellation, patient lookup, slot discovery, and escalation to a human staff member while following the supplied clinic data and response contract.

---

## 1. Project Overview

The Clinic Front Desk Agent exposes a REST API:

```text
POST /agent/run