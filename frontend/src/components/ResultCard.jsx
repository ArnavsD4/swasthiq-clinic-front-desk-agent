import { Check, Cross, Alert, Calendar, Person } from './Icons.jsx'

const REASONS = {
  clinical_urgent: 'Urgent clinical attention required',
  medical_advice: 'Medical advice requires human assistance',
  not_authorised: 'Authorisation is required',
  ambiguous_patient: 'Patient identity needs clarification',
  out_of_scope: 'This request requires human assistance',
}

const CONFIG = {
  booked: { tone: 'success', title: 'Appointment booked', Icon: Check },
  rescheduled: { tone: 'success', title: 'Appointment rescheduled', Icon: Calendar },
  cancelled: { tone: 'neutral', title: 'Appointment cancelled', Icon: Cross },
}

export default function ResultCard({ result }) {
  const { state, reason, appointmentId, patientId } = result

  if (state === 'escalated') {
    return (
      <section className="result tone-care" aria-label="Human assistance required">
        <div className="result-icon"><Person /></div>
        <div className="result-body">
          <h3>Human assistance required</h3>
          <p className="result-reason">{REASONS[reason] || REASONS.out_of_scope}</p>
          <p className="result-hint">A member of the clinic team will take it from here. For anything urgent, please call the clinic directly.</p>
        </div>
      </section>
    )
  }

  const cfg = CONFIG[state]
  if (cfg) {
    const { Icon } = cfg
    return (
      <section className={`result tone-${cfg.tone}`} aria-label={cfg.title}>
        <div className="result-icon"><Icon /></div>
        <div className="result-body">
          <h3>{cfg.title}</h3>
          {(appointmentId || patientId) && (
            <dl className="result-meta">
              {appointmentId && <div><dt>Appointment ID</dt><dd>{appointmentId}</dd></div>}
              {patientId && <div><dt>Patient ID</dt><dd>{patientId}</dd></div>}
            </dl>
          )}
        </div>
      </section>
    )
  }

  if (state === 'refused' || state === 'abandoned') {
    return (
      <section className="result tone-neutral" aria-label="Request closed">
        <div className="result-icon"><Alert /></div>
        <div className="result-body">
          <h3>{state === 'refused' ? 'Request could not be completed' : 'Conversation ended'}</h3>
          <p className="result-hint">You can start a new conversation at any time.</p>
        </div>
      </section>
    )
  }
  return null
}
