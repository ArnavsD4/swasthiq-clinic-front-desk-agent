import ResultCard from './ResultCard.jsx'
import { Alert, Retry } from './Icons.jsx'

export default function Message({ msg, onRetry, canRetry }) {
  const isUser = msg.role === 'user'
  return (
    <article className={`msg ${isUser ? 'user' : 'ai'}`}>
      <div className="msg-col">
        {msg.error ? (
          <div className="bubble error" role="alert">
            <div className="error-head"><Alert width={18} height={18} /> Message not delivered</div>
            <p>{msg.text}</p>
            {canRetry && (
              <button className="btn-ghost" onClick={onRetry}><Retry width={16} height={16} /> Try again</button>
            )}
          </div>
        ) : (
          <div className="bubble">{msg.text}</div>
        )}
        {msg.result && <ResultCard result={msg.result} />}
        <time className="stamp">{msg.time}</time>
      </div>
    </article>
  )
}
