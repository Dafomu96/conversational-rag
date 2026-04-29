import { useState, useRef, useEffect } from 'react'
import Message from './Message'

const SUGGESTIONS = [
  "What is the main topic of this document?",
  "Summarize the key findings.",
  "What tables or data are present?",
  "What conclusions does the document reach?",
]

export default function ChatPanel({ messages, onSend, loading, onSourceClick }) {
  const [input, setInput] = useState('')
  const bottomRef = useRef(null)
  const textareaRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const handleSubmit = () => {
    if (!input.trim() || loading) return
    onSend(input.trim())
    setInput('')
    textareaRef.current?.focus()
  }

  const showSuggestions = messages.length <= 1 && !loading

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-5">
        {messages.map((msg, i) => (
          <Message key={i} msg={msg} onSourceClick={onSourceClick} />
        ))}

        {loading && (
          <div className="flex gap-3 items-start">
            <div className="w-7 h-7 rounded-full bg-[#e8b84b]/20 border border-[#e8b84b]/30 flex items-center justify-center flex-shrink-0 mt-0.5">
              <span className="text-[#e8b84b] text-xs font-bold" style={{ fontFamily: "'Syne', sans-serif" }}>R</span>
            </div>
            <div className="bg-white/4 border border-white/6 rounded-2xl rounded-tl-sm px-4 py-3">
              <div className="flex gap-1.5 items-center">
                {[0, 1, 2].map(i => (
                  <div key={i} className="w-1.5 h-1.5 bg-[#e8b84b] rounded-full animate-bounce"
                    style={{ animationDelay: `${i * 0.15}s` }} />
                ))}
                <span className="text-white/30 text-xs ml-2">Retrieving context...</span>
              </div>
            </div>
          </div>
        )}

        {/* Suggestions */}
        {showSuggestions && (
          <div className="grid grid-cols-2 gap-2 mt-4">
            {SUGGESTIONS.map(s => (
              <button
                key={s}
                onClick={() => onSend(s)}
                className="text-left px-4 py-3 rounded-xl bg-white/3 border border-white/6
                  hover:border-[#e8b84b]/30 hover:bg-[#e8b84b]/5 transition-all text-xs text-white/40
                  hover:text-white/70 leading-relaxed"
              >
                {s}
              </button>
            ))}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div className="border-t border-white/5 p-4 flex-shrink-0">
        <div className="flex gap-3 items-end">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSubmit()
              }
            }}
            placeholder="Ask about the document..."
            rows={2}
            className="flex-1 bg-white/4 border border-white/10 rounded-xl px-4 py-3 text-sm text-white/90
              placeholder-white/20 resize-none focus:outline-none focus:border-[#e8b84b]/40
              focus:bg-white/[0.06] transition-all"
            style={{ fontFamily: "'DM Sans', sans-serif" }}
          />
          <button
            onClick={handleSubmit}
            disabled={!input.trim() || loading}
            className="px-5 py-3 rounded-xl bg-[#e8b84b] text-[#0f0e0c] font-semibold text-sm
              hover:bg-[#d4a535] disabled:opacity-25 disabled:cursor-not-allowed transition-all
              active:scale-95"
          >
            Send
          </button>
        </div>
        <p className="text-white/15 text-xs mt-2 px-1">↵ Send · Shift+↵ New line</p>
      </div>
    </div>
  )
}