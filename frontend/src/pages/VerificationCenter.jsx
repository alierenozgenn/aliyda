import { useState, useEffect } from 'react'
import { getStatements, getDrafts, approveDraft, rejectDraft, finalizeStatement } from '../services/api'
import {
  CheckCircle, XCircle, Clock, FileText, Pencil, X,
  AlertTriangle, ChevronDown, ChevronUp, Shield
} from 'lucide-react'

// ──────────────────────────────────────────────
// Helpers
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

const STATUS_MAP = {
  uploaded: { label: 'Yüklendi', color: 'text-gray-400' },
  extracting: { label: 'İşleniyor...', color: 'text-blue-400' },
  extracted: { label: 'Çıkarıldı', color: 'text-blue-400' },
  pending_review: { label: 'Onay Bekliyor', color: 'text-yellow-400' },
  approved: { label: 'Tamamlandı', color: 'text-emerald-400' },
  saved: { label: 'Kaydedildi', color: 'text-emerald-400' },
  failed: { label: 'Başarısız', color: 'text-red-400' },
}

const CATEGORIES = [
  'Market', 'Restoran/Kafe', 'Ulaşım', 'Faturalar', 'Eğlence',
  'Sağlık', 'Giyim', 'Eğitim', 'Kira', 'Maaş', 'Diğer Gelir',
  'Transfer', 'Alışveriş', 'Teknoloji', 'Spor', 'Diğer',
]

const fmt = (n) => `₺${Number(n).toLocaleString('tr-TR', { minimumFractionDigits: 2 })}`

// ──────────────────────────────────────────────
// Edit Draft Modal
// ──────────────────────────────────────────────
function EditDraftModal({ draft, onSave, onClose }) {
  const [form, setForm] = useState({
    transaction_date: draft.transaction_date || '',
    description: draft.description || '',
    amount: String(draft.amount || ''),
    direction: draft.direction || 'expense',
    category: draft.category || 'Diğer',
    counterparty: draft.counterparty || '',
  })
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-2xl p-6 w-full max-w-lg shadow-2xl">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-white font-semibold text-lg">İşlemi Düzenle ve Onayla</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors">
            <X size={20} />
          </button>
        </div>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-400 mb-1">Tarih</label>
              <input type="date" value={form.transaction_date} onChange={e => set('transaction_date', e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-violet-500" />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Yön</label>
              <select value={form.direction} onChange={e => set('direction', e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm">
                <option value="expense">Gider</option>
                <option value="income">Gelir</option>
                <option value="transfer">Transfer</option>
              </select>
            </div>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Açıklama</label>
            <input type="text" value={form.description} onChange={e => set('description', e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-violet-500" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-400 mb-1">Tutar (₺)</label>
              <input type="number" step="0.01" value={form.amount} onChange={e => set('amount', e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-violet-500" />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Kategori</label>
              <select value={form.category} onChange={e => set('category', e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm">
                {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Karşı Taraf</label>
            <input type="text" value={form.counterparty} onChange={e => set('counterparty', e.target.value)}
              placeholder="Migros, Netflix..."
              className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-violet-500" />
          </div>
          <div className="flex gap-3 pt-1">
            <button onClick={onClose}
              className="flex-1 bg-gray-800 hover:bg-gray-700 text-gray-300 py-2 rounded-lg text-sm transition-colors">
              İptal
            </button>
            <button onClick={() => onSave(form)}
              className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white py-2 rounded-lg text-sm font-medium transition-colors">
              Düzenle ve Onayla
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// ──────────────────────────────────────────────
// Draft Card
// ──────────────────────────────────────────────
function DraftCard({ draft, onApprove, onReject, onEdit }) {
  const confidencePct = draft.confidence_score ? Math.round(draft.confidence_score * 100) : null
  const isLowConfidence = confidencePct !== null && confidencePct < 70

  return (
    <div className={`bg-gray-800/60 border rounded-xl px-5 py-4 transition-all hover:bg-gray-800/80 ${
      isLowConfidence ? 'border-amber-500/30' : 'border-gray-700/50'
    }`}>
      <div className="flex items-start justify-between gap-4">
        {/* Left: Details */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-white font-medium text-sm truncate">{draft.description}</span>
            {isLowConfidence && (
              <span className="inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-400 border border-amber-500/30 shrink-0">
                <AlertTriangle size={10} />Düşük güven
              </span>
            )}
          </div>
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-gray-400 mt-1">
            <span>{draft.transaction_date}</span>
            {draft.transaction_time && <span>{draft.transaction_time.slice(0, 5)}</span>}
            <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
              draft.direction === 'income' ? 'bg-emerald-500/20 text-emerald-400' :
              draft.direction === 'transfer' ? 'bg-blue-500/20 text-blue-400' :
              'bg-red-500/20 text-red-400'
            }`}>
              {draft.direction === 'income' ? 'Gelir' : draft.direction === 'transfer' ? 'Transfer' : 'Gider'}
            </span>
            {draft.category && <span className="text-gray-500">📁 {draft.category}</span>}
            {draft.counterparty && <span className="text-gray-500">👤 {draft.counterparty}</span>}
            {confidencePct !== null && (
              <span className="text-gray-500">🎯 %{confidencePct}</span>
            )}
          </div>
          {draft.original_description && draft.original_description !== draft.description && (
            <p className="text-[11px] text-gray-600 mt-1 truncate italic">
              Orijinal: {draft.original_description}
            </p>
          )}
        </div>

        {/* Right: Amount + Actions */}
        <div className="flex items-center gap-3 shrink-0">
          <span className={`text-sm font-bold px-2 py-1 rounded-md bg-black/20 ${
            draft.direction === 'income' ? 'text-emerald-400' : 'text-red-400'
          }`}>
            {draft.direction === 'income' ? '+' : '-'}{fmt(draft.amount)}
          </span>
          <div className="flex items-center gap-1">
            <button onClick={() => onApprove(draft.id)} title="Onayla"
              className="text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/10 p-1.5 rounded-lg transition-all">
              <CheckCircle size={20} />
            </button>
            <button onClick={() => onEdit(draft)} title="Düzenle ve Onayla"
              className="text-violet-400 hover:text-violet-300 hover:bg-violet-500/10 p-1.5 rounded-lg transition-all">
              <Pencil size={16} />
            </button>
            <button onClick={() => onReject(draft.id)} title="Reddet"
              className="text-red-400 hover:text-red-300 hover:bg-red-500/10 p-1.5 rounded-lg transition-all">
              <XCircle size={20} />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// ──────────────────────────────────────────────
// Main
// ──────────────────────────────────────────────
export default function VerificationCenter() {
  const [month, setMonth] = useState(MONTHS[0])
  const [statements, setStatements] = useState([])
  const [expandedStmt, setExpandedStmt] = useState(null)
  const [drafts, setDrafts] = useState([])
  const [editDraft, setEditDraft] = useState(null)
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [approving, setApproving] = useState(null) // draft id being approved

  const loadStatements = () => {
    setLoading(true)
    getStatements(month)
      .then(res => {
        const list = res.data || []
        setStatements(list)
        // Auto-expand the first pending_review statement
        const pending = list.find(s => s.status === 'pending_review')
        if (pending && !expandedStmt) loadDrafts(pending)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    setExpandedStmt(null)
    setDrafts([])
    setMessage('')
    loadStatements()
  }, [month])

  const loadDrafts = async (stmt) => {
    setExpandedStmt(stmt.id)
    try {
      const res = await getDrafts(stmt.id)
      setDrafts(res.data || [])
    } catch {
      setDrafts([])
    }
  }

  const handleApprove = async (draftId, updates = null) => {
    setApproving(draftId)
    try {
      await approveDraft(draftId, updates)
      setDrafts(prev => prev.filter(d => d.id !== draftId))
      setMessage('')
    } catch (err) {
      setMessage(`❌ Onay hatası: ${err.response?.data?.error?.message || 'Bilinmeyen hata'}`)
    } finally {
      setApproving(null)
    }
  }

  const handleReject = async (draftId) => {
    try {
      await rejectDraft(draftId, 'Kullanıcı tarafından reddedildi.')
      setDrafts(prev => prev.filter(d => d.id !== draftId))
    } catch (err) {
      setMessage(`❌ Red hatası: ${err.response?.data?.error?.message || 'Bilinmeyen hata'}`)
    }
  }

  const handleEditSave = async (form) => {
    if (!editDraft) return
    await handleApprove(editDraft.id, {
      transaction_date: form.transaction_date,
      description: form.description,
      amount: parseFloat(form.amount),
      direction: form.direction,
      category: form.category,
      counterparty: form.counterparty || null,
    })
    setEditDraft(null)
  }

  const handleApproveAll = async () => {
    const safeDrafts = drafts.filter(d => d.confidence_score >= 0.7)
    if (safeDrafts.length === 0) {
      setMessage('⚠ Güvenli onaylanacak işlem yok.')
      return
    }
    setMessage(`⏳ ${safeDrafts.length} güvenli işlem onaylanıyor...`)
    for (const d of safeDrafts) {
      await handleApprove(d.id)
    }
    setMessage(`✅ ${safeDrafts.length} işlem toplu onaylandı.`)
  }

  const handleFinalize = async (stmtId) => {
    try {
      await finalizeStatement(stmtId)
      setMessage('✅ PDF tamamlandı.')
      loadStatements()
    } catch (err) {
      setMessage(`❌ ${err.response?.data?.error?.message || 'Tamamlama hatası'}`)
    }
  }

  const pendingStatements = statements.filter(s => s.status === 'pending_review')
  const lowConfidenceCount = drafts.filter(d => d.confidence_score && d.confidence_score < 0.7).length

  return (
    <div className="p-8 max-w-5xl">
      {/* Edit Modal */}
      {editDraft && (
        <EditDraftModal
          draft={editDraft}
          onSave={handleEditSave}
          onClose={() => setEditDraft(null)}
        />
      )}

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Shield size={22} className="text-violet-400" />
            Doğrulama Merkezi
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            PDF'den çıkarılan işlemleri inceleyin, onaylayın veya reddedin.
          </p>
        </div>
        <select
          value={month}
          onChange={e => setMonth(e.target.value)}
          className="bg-gray-800 border border-gray-700 text-white text-sm rounded-lg px-4 py-2 focus:outline-none focus:border-violet-500"
        >
          {MONTHS.map(m => <option key={m} value={m}>{m}</option>)}
        </select>
      </div>

      {/* Info Banner */}
      <div className="mb-6 glass-panel rounded-xl px-5 py-4">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-lg bg-violet-500/20 text-violet-400 shrink-0 mt-0.5">
            <Shield size={16} />
          </div>
          <div className="text-sm">
            <p className="text-gray-200 font-medium mb-1">AI çıktısı finansal gerçek değildir</p>
            <p className="text-gray-400 text-xs leading-relaxed">
              Gemini tarafından PDF'den çıkarılan işlemler burada gösterilir. Onayladığınız işlemler
              Supabase'e kaydedilir ve dashboard/chatbot'ta kullanılır. Onaylamadığınız işlemler
              finansal verinize dahil olmaz.
            </p>
          </div>
        </div>
      </div>

      {/* Message */}
      {message && (
        <div className={`mb-4 px-4 py-3 rounded-lg text-sm ${
          message.startsWith('✅') ? 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-400' :
          message.startsWith('❌') ? 'bg-red-500/10 border border-red-500/30 text-red-400' :
          'bg-amber-500/10 border border-amber-500/30 text-amber-400'
        }`}>
          {message}
        </div>
      )}

      {/* Loading */}
      {loading && <p className="text-gray-400 text-sm">Yükleniyor...</p>}

      {/* No statements */}
      {!loading && statements.length === 0 && (
        <div className="bg-gray-900 border border-dashed border-gray-700 rounded-xl p-12 text-center">
          <FileText size={36} className="text-gray-600 mx-auto mb-3" />
          <p className="text-gray-400 font-medium">Bu ay için yüklenmiş PDF yok.</p>
          <p className="text-gray-500 text-sm mt-1">
            PDF Yükle sayfasından banka ekstrenizi yükleyin.
          </p>
          <a href="/upload" className="inline-block mt-4 text-sm text-violet-400 hover:text-violet-300">
            PDF Yükle →
          </a>
        </div>
      )}

      {/* Statement List */}
      {statements.length > 0 && (
        <div className="space-y-4">
          {statements.map(stmt => {
            const status = STATUS_MAP[stmt.status] || { label: stmt.status, color: 'text-gray-400' }
            const isExpanded = expandedStmt === stmt.id
            const isPending = stmt.status === 'pending_review'

            return (
              <div key={stmt.id} className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
                {/* Statement Header */}
                <button
                  onClick={() => isPending ? loadDrafts(stmt) : null}
                  className={`w-full flex items-center justify-between px-5 py-4 transition-colors ${
                    isPending ? 'hover:bg-gray-800/50 cursor-pointer' : 'cursor-default'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <FileText size={18} className={status.color} />
                    <div className="text-left">
                      <p className="text-white text-sm font-medium">{stmt.file_name || 'PDF Ekstre'}</p>
                      <p className="text-gray-500 text-xs mt-0.5">
                        {stmt.month} · <span className={status.color}>{status.label}</span>
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {isPending && drafts.length > 0 && isExpanded && (
                      <span className="text-xs text-yellow-400 bg-yellow-500/10 px-2 py-1 rounded-full">
                        {drafts.length} bekliyor
                      </span>
                    )}
                    {!isPending && stmt.status === 'approved' && (
                      <span className="text-xs text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded-full">
                        ✅ Tamamlandı
                      </span>
                    )}
                    {isPending && (isExpanded ? <ChevronUp size={16} className="text-gray-500" /> : <ChevronDown size={16} className="text-gray-500" />)}
                  </div>
                </button>

                {/* Expanded Drafts */}
                {isExpanded && isPending && (
                  <div className="border-t border-gray-800 px-5 py-4">
                    {/* Bulk Actions */}
                    {drafts.length > 0 && (
                      <div className="flex items-center justify-between mb-4">
                        <div className="text-xs text-gray-500">
                          {drafts.length} işlem onay bekliyor
                          {lowConfidenceCount > 0 && (
                            <span className="text-amber-400 ml-2">
                              ({lowConfidenceCount} düşük güvenli)
                            </span>
                          )}
                        </div>
                        <div className="flex gap-2">
                          <button onClick={handleApproveAll}
                            className="text-xs font-medium px-3 py-1.5 rounded-lg bg-emerald-600/20 text-emerald-400 hover:bg-emerald-600/30 transition-colors">
                            Güvenlileri Toplu Onayla
                          </button>
                          {drafts.length === 0 && (
                            <button onClick={() => handleFinalize(stmt.id)}
                              className="text-xs font-medium px-3 py-1.5 rounded-lg bg-violet-600/20 text-violet-400 hover:bg-violet-600/30 transition-colors">
                              PDF'i Tamamla
                            </button>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Draft list */}
                    {drafts.length === 0 ? (
                      <div className="text-center py-6">
                        <p className="text-emerald-400 text-sm font-medium mb-2">✅ Tüm işlemler tamamlandı!</p>
                        <button onClick={() => handleFinalize(stmt.id)}
                          className="text-sm font-medium px-4 py-2 rounded-lg bg-violet-600 hover:bg-violet-700 text-white transition-colors">
                          PDF'i Tamamla ve Dashboard'a Yansıt
                        </button>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {drafts.map(draft => (
                          <DraftCard
                            key={draft.id}
                            draft={draft}
                            onApprove={handleApprove}
                            onReject={handleReject}
                            onEdit={setEditDraft}
                          />
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
