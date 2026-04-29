import { useState, useCallback } from 'react'
import { v4 as uuidv4 } from 'uuid'
import UploadZone from './components/UploadZone'
import ChatPanel from './components/ChatPanel'
import PDFViewer from './components/PDFViewer'
import DocumentStats from './components/DocumentStats'

const SESSION_ID = uuidv4()
const API = 'http://localhost:8000'

export default function App() {
  const [docInfo, setDocInfo] = useState(null)
  const [pdfFile, setPdfFile] = useState(null)
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [activePage, setActivePage] = useState(1)
  const [uploadError, setUploadError] = useState(null)

  const handleUpload = useCallback(async (file) => {
    setUploadError(null)
    setPdfFile(URL.createObjectURL(file))
    const form = new FormData()
    form.append('file', file)
    try {
      const res = await fetch(`${API}/upload`, { method: 'POST', body: form })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setDocInfo(data)
      setMessages([{
        role: 'assistant',
        content: `Document **${data.filename}** loaded successfully.\n\nFound **${data.text_chunks}** text segments and **${data.table_chunks}** tables across **${data.pages}** pages.\n\nAsk me anything about this document.`,
        sources: [],
        grounded: true,
        score: 1.0,
      }])
    } catch (e) {
      setUploadError('Failed to process PDF. Is the backend running?')
      setPdfFile(null)
    }
  }, [])

  const handleChat = useCallback(async (query) => {
    if (!docInfo) return
    setMessages(prev => [...prev, { role: 'user', content: query }])
    setLoading(true)
    try {
      const res = await fetch(`${API}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          session_id: SESSION_ID,
          document_id: docInfo.doc_id,
        }),
      })
      const data = await res.json()
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.answer,
        sources: data.sources,
        grounded: data.is_grounded,
        score: data.hallucination_score,
      }])
      if (data.sources?.[0]?.page) setActivePage(data.sources[0].page)
    } catch (e) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Error connecting to backend. Please check the server.',
        sources: [],
        grounded: false,
        score: 0,
      }])
    } finally {
      setLoading(false)
    }
  }, [docInfo])

  return (
    <div className="min-h-screen bg-[#0f0e0c] text-white flex flex-col" style={{ fontFamily: "'DM Sans', sans-serif" }}>
      {/* Header */}
      <header className="border-b border-white/5 px-8 py-4 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-[#e8b84b] flex items-center justify-center">
            <span className="text-[#0f0e0c] font-bold text-sm" style={{ fontFamily: "'Syne', sans-serif" }}>R</span>
          </div>
          <span className="text-lg font-semibold tracking-tight" style={{ fontFamily: "'Syne', sans-serif" }}>
            DocRAG
          </span>
          <span className="text-white/25 text-sm font-light hidden md:block">— Conversational Document Intelligence</span>
        </div>
        {docInfo && <DocumentStats docInfo={docInfo} />}
      </header>

      {/* Main */}
      <div className="flex flex-1 overflow-hidden">
        {!docInfo ? (
          <div className="flex-1 flex items-center justify-center p-12">
            <UploadZone onUpload={handleUpload} error={uploadError} />
          </div>
        ) : (
          <>
            {/* PDF Sidebar */}
            <div className="w-[400px] border-r border-white/5 flex-shrink-0 overflow-hidden hidden lg:flex lg:flex-col">
              <PDFViewer fileUrl={pdfFile} activePage={activePage} />
            </div>
            {/* Chat */}
            <div className="flex-1 overflow-hidden flex flex-col">
              <ChatPanel
                messages={messages}
                onSend={handleChat}
                loading={loading}
                onSourceClick={setActivePage}
              />
            </div>
          </>
        )}
      </div>
    </div>
  )
}