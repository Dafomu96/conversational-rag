export default function DocumentStats({ docInfo }) {
  return (
    <div className="flex items-center gap-5 text-xs">
      <span className="text-white/30 font-mono truncate max-w-[180px]" title={docInfo.filename}>
        {docInfo.filename}
      </span>
      <div className="flex items-center gap-4">
        <span className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-white/30" />
          <span className="text-white/30">{docInfo.pages}p</span>
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-green-400/60" />
          <span className="text-white/40">{docInfo.text_chunks} text</span>
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-400/60" />
          <span className="text-white/40">{docInfo.table_chunks} tables</span>
        </span>
      </div>
    </div>
  )
}