import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'

export default function UploadZone({ onUpload, error }) {
  const [uploading, setUploading] = useState(false)
  const [fileName, setFileName] = useState(null)

  const onDrop = useCallback(async (files) => {
    if (!files[0]) return
    setFileName(files[0].name)
    setUploading(true)
    try {
      await onUpload(files[0])
    } finally {
      setUploading(false)
    }
  }, [onUpload])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 1,
    disabled: uploading,
  })

  return (
    <div className="w-full max-w-2xl">
      {/* Hero text */}
      <div className="mb-12">
        <h1 className="text-6xl font-bold leading-[1.05] tracking-tight mb-4" style={{ fontFamily: "'Syne', sans-serif" }}>
          Ask your<br />
          <span className="text-[#e8b84b]">documents</span><br />
          anything.
        </h1>
        <p className="text-white/40 text-lg font-light max-w-md">
          Hybrid RAG with table extraction, conversational memory, and hallucination detection.
        </p>
      </div>

      {/* Drop zone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-300
          ${isDragActive
            ? 'border-[#e8b84b] bg-[#e8b84b]/5 scale-[1.01]'
            : uploading
              ? 'border-white/20 bg-white/2 cursor-wait'
              : 'border-white/10 hover:border-white/25 hover:bg-white/[0.02]'
          }`}
      >
        <input {...getInputProps()} />

        {uploading ? (
          <div className="flex flex-col items-center gap-4">
            <div className="w-10 h-10 border-2 border-[#e8b84b] border-t-transparent rounded-full animate-spin" />
            <div>
              <p className="text-white/70 font-medium">Processing {fileName}</p>
              <p className="text-white/30 text-sm mt-1">Extracting text and tables...</p>
            </div>
          </div>
        ) : isDragActive ? (
          <div className="flex flex-col items-center gap-3">
            <div className="text-4xl">📥</div>
            <p className="text-[#e8b84b] font-medium">Drop to analyze</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center text-2xl">
              📄
            </div>
            <div>
              <p className="text-white/70 font-medium">Drag & drop a PDF here</p>
              <p className="text-white/30 text-sm mt-1">or click to select · technical, financial, scientific reports</p>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-4 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          ⚠️ {error}
        </div>
      )}

      {/* Feature pills */}
      <div className="mt-8 flex flex-wrap gap-2">
        {[
          { label: 'BM25 + Semantic hybrid', color: 'text-[#e8b84b]' },
          { label: 'Table-aware chunking', color: 'text-blue-400' },
          { label: 'Cross-encoder reranking', color: 'text-green-400' },
          { label: 'Query expansion', color: 'text-purple-400' },
          { label: 'Hallucination check', color: 'text-orange-400' },
          { label: 'Session memory', color: 'text-pink-400' },
        ].map(({ label, color }) => (
          <span key={label} className="px-3 py-1.5 rounded-full bg-white/4 border border-white/8 text-xs text-white/50 flex items-center gap-1.5">
            <span className={`w-1.5 h-1.5 rounded-full bg-current ${color}`} />
            {label}
          </span>
        ))}
      </div>
    </div>
  )
}