import { useCallback, useEffect, useRef, useState } from 'react'
import Sidebar from './components/Sidebar.jsx'
import Message from './components/Message.jsx'
import Composer from './components/Composer.jsx'
import { Logo, Plus, Menu } from './components/Icons.jsx'
import { runAgent, newConversationId } from './api.js'

const SUGGESTIONS = [
  { label: 'Book an appointment', text: 'I want to book an appointment' },
  { label: 'Reschedule my appointment', text: 'I want to reschedule my appointment' },
  { label: 'Cancel my appointment', text: 'I want to cancel my appointment' },
  { label: 'Find available slots', text: 'What appointment slots are available?' },
]

const now = () => new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
let uid = 0
const mid = () => `m${++uid}`

export default function App() {
  const [conversationId, setConversationId] = useState(newConversationId)
  const [turns, setTurns] = useState([])        // user messages only, sent in full on every request
  const [messages, setMessages] = useState([])  // what is rendered
  const [loading, setLoading] = useState(false)
  const [navOpen, setNavOpen] = useState(false)
  const [resetCount, setResetCount] = useState(0)
  const endRef = useRef(null)
  const activeRef = useRef(conversationId)
  activeRef.current = conversationId

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, loading])

  const request = useCallback(async (id, allTurns) => {
    setLoading(true)
    try {
      const r = await runAgent(id, allTurns)
      if (activeRef.current !== id) return
      setMessages((m) => [
        ...m.filter((x) => !x.error),
        { id: mid(), role: 'ai', text: r.reply, time: now(), result: r.state ? r : null },
      ])
    } catch (err) {
      if (activeRef.current !== id) return
      setMessages((m) => [
        ...m.filter((x) => !x.error),
        { id: mid(), role: 'ai', error: true, text: err.message, time: now() },
      ])
    } finally {
      if (activeRef.current === id) setLoading(false)
    }
  }, [])

  const send = (text) => {
    if (loading) return
    const next = [...turns, text]
    setTurns(next)
    setMessages((m) => [...m.filter((x) => !x.error), { id: mid(), role: 'user', text, time: now() }])
    request(conversationId, next)
  }

  const retry = () => { if (!loading && turns.length) request(conversationId, turns) }

  const reset = () => {
    const id = newConversationId()
    activeRef.current = id
    setConversationId(id)
    setTurns([])
    setMessages([])
    setLoading(false)
    setResetCount((c) => c + 1)
  }

  const started = messages.length > 0
  const last = messages[messages.length - 1]
  const finished = last && last.result

  return (
    <div className="app">
      <Sidebar open={navOpen} onClose={() => setNavOpen(false)} conversationId={conversationId} started={started} onNew={reset} disabled={false} />

      <main className="main">
        <header className="topbar">
          <button className="icon-btn menu-btn" onClick={() => setNavOpen(true)} aria-label="Open navigation"><Menu /></button>
          <div className="topbar-title">
            <h1>Sunrise Clinic</h1>
            <span className="muted">AI Front Desk</span>
          </div>
          <span className="status" role="status"><span className="dot live" /> Ready</span>
          <button className="btn-outline" onClick={reset}><Plus width={16} height={16} /> <span>New conversation</span></button>
        </header>

        <div className="chat" role="log" aria-live="polite" aria-label="Conversation">
          {!started ? (
            <div className="empty">
              <Logo size={56} />
              <h2>How can we help today?</h2>
              <p>Book, reschedule or cancel an appointment at Sunrise Clinic, Dehradun. This assistant handles front-desk requests only and cannot give medical advice.</p>
              <div className="chips">
                {SUGGESTIONS.map((s) => (
                  <button key={s.label} className="chip" onClick={() => send(s.text)}>{s.label}</button>
                ))}
              </div>
            </div>
          ) : (
            <div className="thread">
              {messages.map((m) => (
                <Message key={m.id} msg={m} onRetry={retry} canRetry={!loading && m === last} />
              ))}
              {loading && (
                <article className="msg ai" aria-label="Front desk is typing">
                  <div className="msg-col"><div className="bubble typing"><i /><i /><i /></div></div>
                </article>
              )}
              <div ref={endRef} />
            </div>
          )}
        </div>

        <div className="dock">
          {finished && !loading && (
            <p className="finish-note">This request is complete. <button className="link" onClick={reset}>Start a new conversation</button> for something else.</p>
          )}
          <Composer onSend={send} disabled={loading} focusKey={resetCount} />
        </div>
      </main>
    </div>
  )
}
