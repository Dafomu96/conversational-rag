export default function Message({ msg, onSourceClick }) {
  const isUser = msg.role === 'user'

  const formatContent = (text) => {
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong class="text-white/90">$1</strong>')
      .replace(/\[Source (\d+)\]/g,
        '<span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-[#e8b84b]/15 border border-[#e8b84b]/25 text-[#e8b84b] text-xs font-mono cursor-default">[S$1]</span>')
      .replace(/\n/g, '<br/>')
  }

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* Avatar */}
      <div className={`w-7 h-7 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-bold mt-0.5
        ${isUser
          ? 'bg-white/10 border border-white/15 text-white/50'
          : 'bg-[#e8b84b]/20 border border-[#e8b84b]/30 text-[#e8b84b]'
        }`}
        style={{ fontFamily: "'Syne', sans-serif" }}
      >
        {isUser ? 'U' : 'R'}
      </div>

      <div className={`flex flex-col gap-2 max-w-[80%] ${isUser ? 'items-end' : 'items-start'}`}>
        {/* Bubble */}
        <div
          className={`rounded-2xl px-4 py-3 text-sm leading-relaxed
            ${isUser
              ? 'bg-[#e8b84b]/10 border border-[#e8b84b]/15 text-white/85 rounded-tr-sm'
              : 'bg-white/[0.04] border border-white/[0.06] text-white/75 rounded-tl-sm'
            }`}
          dangerouslySetInnerHTML={{ __html: formatContent(msg.content) }}
          style={{ fontFamily: "'DM Sans', sans-serif" }}
        />

        {/* Sources */}
        {msg.sources?.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            <span className="text-white/20 text-xs self-center">Sources:</span>
            {msg.sources.map((s, i) => (
              <button
                key={i}
                onClick={() => onSourceClick && onSourceClick(s.page)}
                title={s.section || ''}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg
                  bg-white/4 border border-white/8 hover:border-[#e8b84b]/30
                  hover:bg-[#e8b84b]/5 transition-all text-xs text-white/40 hover:text-white/70"
              >
                <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0
                  ${s.type === 'table' ? 'bg-blue-400' : 'bg-green-400'}`}
                />
                <span>p.{s.page}</span>
                <span className="text-white/20">{s.type}</span>
                {s.score && (
                  <span className="text-white/20 font-mono text-[10px]">
                    {(s.score * 100).toFixed(0)}%
                  </span>
                )}
              </button>
            ))}
          </div>
        )}

        {/* Grounding badge */}
        {msg.score !== undefined && msg.role === 'assistant' && msg.sources?.length > 0 && (
          <div className={`flex items-center gap-1.5 text-[11px]
            ${msg.grounded ? 'text-green-400/40' : 'text-red-400/50'}`}
          >
            <div className={`w-1 h-1 rounded-full
              ${msg.grounded ? 'bg-green-400' : 'bg-red-400'}`}
            />
            Grounding score: {(msg.score * 100).toFixed(0)}%
          </div>
        )}
      </div>
    </div>
  )
}