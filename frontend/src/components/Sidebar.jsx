import { Logo, Plus, Person, Pin, Calendar } from './Icons.jsx'

const DOCTORS = [
  { name: 'Dr. Anjali Rao', role: 'General Physician' },
  { name: 'Dr. Vikram Sethi', role: 'Paediatrics' },
]

export default function Sidebar({ open, onClose, conversationId, started, onNew, disabled }) {
  return (
    <>
      <div className={`scrim ${open ? 'show' : ''}`} onClick={onClose} aria-hidden="true" />
      <aside className={`sidebar ${open ? 'open' : ''}`} aria-label="Clinic navigation">
        <div className="brand">
          <Logo />
          <div>
            <div className="brand-name">Sunrise Clinic</div>
            <div className="brand-sub">AI Front Desk</div>
          </div>
        </div>

        <button className="btn-primary" onClick={() => { onNew(); onClose() }} disabled={disabled}>
          <Plus /> New conversation
        </button>

        <nav className="side-section" aria-label="Conversations">
          <h2>Current conversation</h2>
          <div className="convo-item" aria-current="true">
            <span className={`dot ${started ? 'live' : ''}`} />
            <div>
              <div className="convo-title">{started ? 'Front desk request' : 'New conversation'}</div>
              <div className="convo-id">{conversationId}</div>
            </div>
          </div>
        </nav>

        <section className="side-section" aria-label="Doctors available">
          <h2>Doctors available</h2>
          <ul className="doctors">
            {DOCTORS.map((d) => (
              <li key={d.name}>
                <span className="avatar"><Person width={18} height={18} /></span>
                <div>
                  <div className="doc-name">{d.name}</div>
                  <div className="doc-role">{d.role}</div>
                </div>
              </li>
            ))}
          </ul>
        </section>

        <section className="side-section" aria-label="Clinic information">
          <h2>Clinic information</h2>
          <div className="info-row"><Pin width={16} height={16} /> Dehradun</div>
          <div className="info-row"><Calendar width={16} height={16} /> Appointments, changes and cancellations</div>
        </section>

        <p className="side-note">Administrative assistant only. It cannot give medical advice or diagnosis.</p>
      </aside>
    </>
  )
}
