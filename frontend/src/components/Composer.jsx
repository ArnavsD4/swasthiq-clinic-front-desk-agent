import { useEffect, useRef, useState } from 'react'
import { Send } from './Icons.jsx'

export default function Composer({ onSend, disabled, focusKey }) {
  const [value, setValue] = useState('')
  const ref = useRef(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 160) + 'px'
  }, [value])

  useEffect(() => { if (!disabled) ref.current?.focus() }, [disabled, focusKey])

  const submit = () => {
    const text = value.trim()
    if (!text || disabled) return
    onSend(text)
    setValue('')
  }

  return (
    <div className="composer">
      <label htmlFor="chat-input" className="sr-only">Message to the front desk</label>
      <textarea
        id="chat-input"
        ref={ref}
        rows={1}
        value={value}
        disabled={disabled}
        placeholder="Type your message…"
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
            e.preventDefault()
            submit()
          }
        }}
      />
      <button className="send" onClick={submit} disabled={disabled || !value.trim()} aria-label="Send message">
        <Send />
      </button>
      <p className="composer-hint">Enter to send · Shift+Enter for a new line</p>
    </div>
  )
}
