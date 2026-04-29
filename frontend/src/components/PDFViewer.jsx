export default function PDFViewer({ fileUrl, activePage }) {
  return (
    <div className="flex flex-col h-full bg-[#1a1814]">
      {/* Header */}
      <div className="px-4 py-3 border-b border-white/5 flex items-center justify-between flex-shrink-0">
        <span className="text-white/30 text-xs font-mono tracking-widest">PDF VIEWER</span>
        <div className="flex items-center gap-2">
          <span className="text-white/20 text-xs">page</span>
          <span className="text-[#e8b84b] text-xs font-mono font-semibold">{activePage}</span>
        </div>
      </div>

      {/* Viewer */}
      <div className="flex-1 overflow-hidden">
        {fileUrl ? (
          <iframe
            src={`${fileUrl}#page=${activePage}&toolbar=0&navpanes=0&scrollbar=0`}
            className="w-full h-full"
            style={{ border: 'none' }}
            title="PDF Document"
          />
        ) : (
          <div className="flex flex-col items-center justify-center h-full gap-3 text-white/15">
            <div className="text-4xl">📄</div>
            <p className="text-sm">No document loaded</p>
          </div>
        )}
      </div>
    </div>
  )
}