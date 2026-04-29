function renderContent(text) {
  // Detectar bloques de tabla markdown y convertirlos a HTML
  const tableRegex = /(\|.+\|\n\|[-| :]+\|\n(?:\|.+\|\n?)*)/g
  const parts = []
  let lastIndex = 0
  let match

  while ((match = tableRegex.exec(text)) !== null) {
    // Texto antes de la tabla
    if (match.index > lastIndex) {
      parts.push({ type: 'text', content: text.slice(lastIndex, match.index) })
    }
    parts.push({ type: 'table', content: match[0] })
    lastIndex = match.index + match[0].length
  }

  if (lastIndex < text.length) {
    parts.push({ type: 'text', content: text.slice(lastIndex) })
  }

  return parts.length > 0 ? parts : [{ type: 'text', content: text }]
}

function MarkdownTable({ raw }) {
  const lines = raw.trim().split('\n').filter(l => !l.match(/^\|[-| :]+\|$/))
  const rows = lines.map(l =>
    l.split('|').filter((_, i, a) => i > 0 && i < a.length - 1).map(c => c.trim())
  )
  const [header, ...body] = rows

  return (
    <div className="overflow-x-auto my-2 rounded-lg border border-white/10">
      <table className="w-full text-xs">
        <thead>
          <tr className="bg-blue-400/10 border-b border-white/10">
            {header.map((h, i) => (
              <th key={i} className="px-3 py-2 text-left text-blue-300/80 font-semibold whitespace-nowrap">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {body.map((row, i) => (
            <tr key={i} className={`border-b border-white/5 ${i % 2 === 0 ? 'bg-white/[0.02]' : ''}`}>
              {row.map((cell, j) => (
                <td key={j} className="px-3 py-2 text-white/60 font-mono text-[11px]">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function formatInlineText(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong class="text-white/90">$1</strong>')
    .replace(/\[Source (\d+)\]/g,
      '<span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-[#e8b84b]/15 border border-[#e8b84b]/25 text-[#e8b84b] text-xs font-mono">[S$1]</span>')
    .replace(/\n/g, '<br/>')
}

export default function Message({ msg, onSourceClick }) {
  const isUser = msg.role === 'user'
  const parts = renderContent(msg.content)

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
        <div className={`rounded-2xl px-4 py-3 text-sm leading-relaxed w-full
          ${isUser
            ? 'bg-[#e8b84b]/10 border border-[#e8b84b]/15 text-white/85 rounded-tr-sm'
            : 'bg-white/[0.04] border border-white/[0.06] text-white/75 rounded-tl-sm'
          }`}
          style={{ fontFamily: "'DM Sans', sans-serif" }}
        >
          {parts.map((part, i) =>
            part.type === 'table'
              ? <MarkdownTable key={i} raw={part.content} />
              : <span key={i} dangerouslySetInnerHTML={{ __html: formatInlineText(part.content) }} />
          )}
        </div>

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
                  ${s.type === 'table' ? 'bg-blue-400' : 'bg-green-400'}`} />
                <span>p.{s.page}</span>
                <span className="text-white/20">{s.type}</span>
                {s.score > 0 && (
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
            ${msg.grounded ? 'text-green-400/40' : 'text-red-400/50'}`}>
            <div className={`w-1 h-1 rounded-full ${msg.grounded ? 'bg-green-400' : 'bg-red-400'}`} />
            Grounding score: {(msg.score * 100).toFixed(0)}%
          </div>
        )}
      </div>
    </div>
  )
}