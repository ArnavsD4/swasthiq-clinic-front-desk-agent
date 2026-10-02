const API_URL = '/api'

// The assignment fixes "today"; never use the browser clock.
export const TODAY = '2026-10-01'

export const TERMINAL_STATES = ['booked', 'rescheduled', 'cancelled', 'escalated', 'refused', 'abandoned']

export function newConversationId() {
  const rand = Math.random().toString(36).slice(2, 8)
  return `cv_${Date.now().toString(36)}${rand}`
}

const str = (v) => (typeof v === 'string' && v.trim() ? v : null)

// Defensive normalisation: the UI never sees undefined or malformed fields.
function normalise(data) {
  if (!data || typeof data !== 'object' || Array.isArray(data)) {
    throw new Error('The server sent a response the app could not read.')
  }
  const state = TERMINAL_STATES.includes(data.terminal_state) ? data.terminal_state : null
  const reply = str(data.reply)
  if (!reply && !state) throw new Error('The server sent an empty response.')
  return {
    reply: reply || 'Your request has been processed.',
    state,
    reason: str(data.escalation_reason),
    patientId: str(data.patient_id),
    appointmentId: str(data.appointment_id),
  }
}

export async function runAgent(conversationId, turns) {
  let res
  try {
    res = await fetch(`${API_URL}/agent/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ conversation_id: conversationId, today: TODAY, turns }),
    })
  } catch {
    throw new Error('Could not reach the front desk service. Check that the backend is running.')
  }
  if (!res.ok) throw new Error(`The front desk service returned an error (${res.status}).`)
  let data
  try {
    data = await res.json()
  } catch {
    throw new Error('The server sent a response the app could not read.')
  }
  return normalise(data)
}
