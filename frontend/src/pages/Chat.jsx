import { useState, useEffect, useRef } from 'react'
import { createChatSession, sendChatMessage } from '../services/api'
import { Send, Sparkles, Bot, User, RefreshCw } from 'lucide-react'

// ──────────────────────────────────────────────
// Constants
// ──────────────────────────────────────────────
function buildMonths() {
  const months = []
  const now = new Date()
  for (let i = 0; i < 12; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
    months.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`)
  }
  return months
}
const MONTHS = buildMonths()

const SUGGESTIONS = [
  { text: 'Bu ay en çok nereye harcamışım?', emoji: '📊' },
  { text: 'Nereden tasarruf edebilirim?', emoji: '💰' },
  { text: 'Ay sonunda ne kadar kalır?', emoji: '📅' },
  { text: 'En büyük harcamalarım neler?', emoji: '🏷️' },
  { text: 'Yemek harcamam fazla mı?', emoji: '🍕' },
]

// ──────────────────────────────────────────────
// Message bubble
// ──────────────────────────────────────────────
function MessageBubble({ msg }) {
  const isUser = msg.role === 'user'
  return (
    <div className={`flex items-end gap-2 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* Avatar */}
      <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 ${
        isUser ? 'bg-violet-600' : 'bg-gray-700'
      }`}>
        {isUser ? <User size={14} /> : <Bot size={14} className="text-violet-300" />}
      </div>
      {/* Bubble */}
      <div
        className={`max-w-lg px-4 py-3 rounded-2xl text-sm leading-relaxed ${
          isUser
            ? 'bg-violet-600 text-white rounded-br-sm'
            : 'bg-gray-800 text-gray-200 rounded-bl-sm border border-gray-700/50'
        }`}
      >
        {msg.content}
      </div>
    </div>
  )
}

// ──────────────────────────────────────────────
// Main
// ──────────────────────────────────────────────
export default function Chat() {
  const [month, setMonth] = useState(MONTHS[0])
  const [sessionId, setSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const startSession = async () => {
    const res = await createChatSession(month)
    const id = res.data?.session_id
    setSessionId(id)
    return id
  }

  const sendMessage = async (text) => {
    if (!text.trim() || loading) return
    setInput('')
    setError('')
    setLoading(true)

    const sid = sessionId || await startSession()

    // Optimistic UI
    setMessages(prev => [...prev, { role: 'user', content: text }])

    try {
      const res = await sendChatMessage({ session_id: sid, message: text, month })
      const answer = res.data?.answer || 'Cevap alınamadı.'
      setMessages(prev => [...prev, { role: 'assistant', content: answer }])
    } catch {
      setError('Mesaj gönderilemedi. Backend çalışıyor mu?')
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Bir hata oluştu. Lütfen tekrar deneyin.',
      }])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  const handleMonthChange = (m) => {
    setMonth(m)
    setSessionId(null)
    setMessages([])
    setError('')
  }

  const handleReset = () => {
    setSessionId(null)
    setMessages([])
    setError('')
  }

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800 bg-gray-900/80 backdrop-blur-sm shrink-0">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-violet-500/20">
            <Sparkles size={16} className="text-violet-400" />
          </div>
          <div>
            <h1 className="text-white font-semibold">Aliyda Chatbot</h1>
            <p className="text-gray-500 text-xs">Doğrulanmış verilerinize göre cevaplar</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={month}
            onChange={e => handleMonthChange(e.target.value)}
            className="bg-gray-800 border border-gray-700 text-white text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:border-violet-500"
          >
            {MONTHS.map(m => <option key={m} value={m}>{m}</option>)}
          </select>
          {messages.length > 0 && (
            <button
              onClick={handleReset}
              title="Yeni sohbet"
              className="p-1.5 text-gray-500 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
            >
              <RefreshCw size={15} />
            </button>
          )}
        </div>
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-6 py-5 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full pb-8">
            <div className="p-4 rounded-2xl bg-violet-500/10 border border-violet-500/20 mb-4">
              <Sparkles size={28} className="text-violet-400" />
            </div>
            <h2 className="text-white font-semibold mb-1">Nasıl yardımcı olabilirim?</h2>
            <p className="text-gray-500 text-sm mb-6 text-center max-w-sm">
              {month} ayına ait doğrulanmış finansal verilerinize göre cevap veririm.
            </p>
            <div className="grid grid-cols-1 gap-2 w-full max-w-sm">
              {SUGGESTIONS.map(s => (
                <button
                  key={s.text}
                  onClick={() => sendMessage(s.text)}
                  className="flex items-center gap-3 bg-gray-800 hover:bg-gray-700 border border-gray-700 hover:border-violet-500/50 text-gray-300 text-sm px-4 py-3 rounded-xl transition-all text-left"
                >
                  <span className="text-base">{s.emoji}</span>
                  {s.text}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <MessageBubble key={i} msg={msg} />
        ))}

        {loading && (
          <div className="flex items-end gap-2">
            <div className="w-7 h-7 rounded-full flex items-center justify-center bg-gray-700 shrink-0">
              <Bot size={14} className="text-violet-300" />
            </div>
            <div className="bg-gray-800 border border-gray-700/50 px-4 py-3 rounded-2xl rounded-bl-sm">
              <div className="flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-1.5 h-1.5 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-1.5 h-1.5 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Error */}
      {error && (
        <div className="mx-6 mb-2 text-xs text-red-400 text-center">{error}</div>
      )}

      {/* Input */}
      <div className="px-6 pb-6 pt-2 shrink-0">
        <div className="flex gap-3 bg-gray-800 border border-gray-700 rounded-2xl p-2 focus-within:border-violet-500 transition-colors">
          <input
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage(input)}
            placeholder={`${month} ayı için bir şey sor...`}
            className="flex-1 bg-transparent text-white text-sm px-2 py-1 focus:outline-none placeholder-gray-500"
          />
          <button
            onClick={() => sendMessage(input)}
            disabled={loading || !input.trim()}
            className="bg-violet-600 hover:bg-violet-700 disabled:opacity-40 disabled:cursor-not-allowed text-white px-4 py-2 rounded-xl transition-colors flex items-center gap-1.5 text-sm font-medium"
          >
            <Send size={15} />
          </button>
        </div>
        <p className="text-center text-xs text-gray-600 mt-2">
          Cevaplar yalnızca doğrulanmış Supabase verinize dayanır.
        </p>
      </div>
    </div>
  )
}
