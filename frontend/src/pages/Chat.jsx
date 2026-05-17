import { useState, useEffect, useRef } from 'react'
import { createChatSession, sendChatMessage, getSessionMessages } from '../services/api'
import { Send, Sparkles } from 'lucide-react'

const MONTHS = ['2026-05', '2026-04', '2026-03', '2026-02']

const SUGGESTIONS = [
  'Bu ay en çok nereye harcamışım?',
  'Nereden tasarruf edebilirim?',
  'Ay sonunda ne kadar kalır?',
  'En büyük harcamalarım neler?',
]

export default function Chat() {
  const [month, setMonth] = useState('2026-05')
  const [sessionId, setSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const startSession = async () => {
    const res = await createChatSession(month)
    const id = res.data?.session_id
    setSessionId(id)
    setMessages([])
    return id
  }

  const sendMessage = async (text) => {
    if (!text.trim() || loading) return
    setInput('')
    setLoading(true)

    const sid = sessionId || await startSession()

    // Optimistic UI — add user message immediately
    setMessages(prev => [...prev, { role: 'user', content: text }])

    try {
      const res = await sendChatMessage({ session_id: sid, message: text, month })
      const answer = res.data?.answer || 'Cevap alınamadı.'
      setMessages(prev => [...prev, { role: 'assistant', content: answer }])
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Bir hata oluştu.' }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-screen p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Sparkles size={22} className="text-violet-400" />
          Chatbot
        </h1>
        <select
          value={month}
          onChange={e => { setMonth(e.target.value); setSessionId(null); setMessages([]) }}
          className="bg-gray-800 border border-gray-700 text-white text-sm rounded-lg px-4 py-2"
        >
          {MONTHS.map(m => <option key={m} value={m}>{m}</option>)}
        </select>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-1">
        {messages.length === 0 && (
          <div className="text-center pt-10">
            <p className="text-gray-500 text-sm mb-6">Sormak istediğin bir şey mi var?</p>
            <div className="flex flex-wrap gap-2 justify-center">
              {SUGGESTIONS.map(s => (
                <button
                  key={s}
                  onClick={() => sendMessage(s)}
                  className="bg-gray-800 border border-gray-700 text-gray-300 text-sm px-4 py-2 rounded-full hover:bg-gray-700 transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-lg px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-violet-600 text-white rounded-br-sm'
                  : 'bg-gray-800 text-gray-200 rounded-bl-sm'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-800 text-gray-400 px-4 py-3 rounded-2xl rounded-bl-sm text-sm">
              Düşünüyor...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="flex gap-3">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && sendMessage(input)}
          placeholder="Bir şey sor..."
          className="flex-1 bg-gray-800 border border-gray-700 text-white rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-violet-500"
        />
        <button
          onClick={() => sendMessage(input)}
          disabled={loading || !input.trim()}
          className="bg-violet-600 hover:bg-violet-700 disabled:opacity-50 text-white px-4 py-3 rounded-xl transition-colors"
        >
          <Send size={18} />
        </button>
      </div>
    </div>
  )
}
