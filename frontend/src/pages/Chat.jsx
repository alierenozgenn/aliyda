import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { createChatSession, sendChatMessage } from '../services/api'
import { Send, Sparkles, Bot, User, RefreshCw, FileUp, ShieldCheck, ListChecks } from 'lucide-react'

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
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-8 py-4 border-b border-gray-800/50 glass shrink-0 z-10 relative">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-gradient-to-br from-violet-500/20 to-fuchsia-500/20 border border-violet-500/20 shadow-[0_0_15px_rgba(139,92,246,0.15)]">
            <Sparkles size={18} className="text-violet-400" />
          </div>
          <div>
            <h1 className="text-white font-bold tracking-wide">Aliyda Chatbot</h1>
            <p className="text-gray-400 text-xs mt-0.5 tracking-wider uppercase font-medium">Doğrulanmış veriler</p>
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
              <RefreshCw size={15} className="group-hover:rotate-180 transition-transform duration-500" />
            </button>
          )}
        </div>
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-6 py-5 space-y-4 w-full max-w-6xl mx-auto">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full pb-8">
            <div className="p-5 rounded-3xl glass-panel mb-5 animate-float shadow-[0_0_30px_rgba(139,92,246,0.15)]">
              <Sparkles size={32} className="text-violet-400 drop-shadow-md" />
            </div>
            <h2 className="text-2xl font-bold bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent mb-2">Nasıl yardımcı olabilirim?</h2>
            <p className="text-gray-400 text-sm mb-8 text-center max-w-sm leading-relaxed">
              {month} ayına ait doğrulanmış finansal verilerinize göre cevap veririm.
            </p>
            <div className="grid grid-cols-3 gap-2 w-full max-w-xl mb-6">
              <Link
                to="/upload"
                className="rounded-xl border border-white/5 bg-white/[0.03] hover:border-violet-500/30 px-3 py-3 text-center transition-colors"
              >
                <FileUp size={16} className="text-violet-300 mx-auto mb-1" />
                <span className="text-[11px] text-gray-300 font-medium">PDF yükle</span>
              </Link>
              <Link
                to="/verify"
                className="rounded-xl border border-white/5 bg-white/[0.03] hover:border-violet-500/30 px-3 py-3 text-center transition-colors"
              >
                <ShieldCheck size={16} className="text-violet-300 mx-auto mb-1" />
                <span className="text-[11px] text-gray-300 font-medium">Doğrula</span>
              </Link>
              <Link
                to="/transactions"
                className="rounded-xl border border-white/5 bg-white/[0.03] hover:border-violet-500/30 px-3 py-3 text-center transition-colors"
              >
                <ListChecks size={16} className="text-violet-300 mx-auto mb-1" />
                <span className="text-[11px] text-gray-300 font-medium">İşlemleri gör</span>
              </Link>
            </div>
            <div className="grid grid-cols-1 gap-3 w-full max-w-sm">
              {SUGGESTIONS.map(s => (
                <button
                  key={s.text}
                  onClick={() => sendMessage(s.text)}
                  className="flex items-center gap-4 glass hover:bg-white/5 border border-white/5 hover:border-violet-500/30 text-gray-300 text-sm px-5 py-3.5 rounded-2xl transition-all duration-300 text-left hover-glow group"
                >
                  <span className="text-lg group-hover:scale-110 transition-transform">{s.emoji}</span>
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
      <div className="w-full max-w-6xl mx-auto px-6 pb-6 pt-2 shrink-0 bg-transparent relative z-10">
        <div className="flex gap-3 glass-panel rounded-2xl p-2.5 shadow-lg focus-within:shadow-[0_0_20px_rgba(139,92,246,0.2)] focus-within:border-violet-500/50 transition-all duration-300">
          <input
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage(input)}
            placeholder={`${month} ayı için bir şey sor...`}
            className="flex-1 bg-transparent text-white text-[15px] px-3 py-1 focus:outline-none placeholder-gray-500"
          />
          <button
            onClick={() => sendMessage(input)}
            disabled={loading || !input.trim()}
            className="bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white px-5 py-2.5 rounded-xl transition-all shadow-md flex items-center gap-2 text-sm font-semibold"
          >
            <Send size={16} />
          </button>
        </div>
        <p className="text-center text-xs text-gray-600 mt-2">
          Cevaplar yalnızca doğrulanmış Supabase verinize dayanır.
        </p>
      </div>
    </div>
  )
}
