export default function Message({ message }) {
  const isUser = message.role === "user";
  return (
    <div className={`message ${isUser ? "message--user" : "message--assistant"} ${message.error ? "message--error" : ""}`}>
      <div className="message-avatar">
        {isUser ? (
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="8" cy="5" r="3" stroke="currentColor" strokeWidth="1.5"/>
            <path d="M2 14c0-3.314 2.686-6 6-6s6 2.686 6 6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
        ) : (
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <rect x="2" y="2" width="5" height="7" rx="1" fill="currentColor" opacity=".8"/>
            <rect x="9" y="2" width="5" height="4" rx="1" fill="currentColor" opacity=".5"/>
            <rect x="9" y="8" width="5" height="6" rx="1" fill="currentColor" opacity=".65"/>
            <rect x="2" y="11" width="5" height="3" rx="1" fill="currentColor" opacity=".55"/>
          </svg>
        )}
      </div>
      <div className="message-body">
        <div className="message-text">
          {message.content || (message.streaming ? <span className="typing-dots"><span/><span/><span/></span> : "")}
        </div>
        {message.streaming && message.content && (
          <span className="cursor-blink">▌</span>
        )}
      </div>
    </div>
  );
}
