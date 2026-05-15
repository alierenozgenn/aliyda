import { useState } from 'react'

export function TransactionCard({ transaction, onVerify, categories = [] }) {
  const [desc, setDesc] = useState(transaction.description || '')
  const [catId, setCatId] = useState(transaction.category_id || '')
  
  return (
    <div className="border rounded-xl p-4 bg-white flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
      <div className="flex-1 w-full">
        <p className="text-xs text-gray-400 font-mono mb-2 bg-gray-50 p-2 rounded border">{transaction.raw_text || 'Orijinal metin bulunamadı'}</p>
        <div className="flex gap-2 w-full mb-2">
          <input 
            className="border rounded p-2 w-full text-sm font-medium" 
            value={desc} 
            onChange={e => setDesc(e.target.value)}
            placeholder="İşlem Açıklaması"
          />
          <select 
            className="border rounded p-2 text-sm text-gray-700 bg-white"
            value={catId}
            onChange={e => setCatId(e.target.value)}
          >
            <option value="">Kategori Seçin</option>
            {categories.map(c => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-3 text-sm text-gray-500">
          <span>{transaction.date}</span>
          <span className={`font-bold ${transaction.direction === 'income' ? 'text-green-600' : 'text-red-600'}`}>
            {transaction.amount} TL
          </span>
          <span className="text-xs px-2 py-1 bg-gray-100 rounded-full border">
            Güven: %{Math.round(transaction.confidence * 100)}
          </span>
        </div>
      </div>
      <div>
        <button 
          onClick={() => onVerify({ description: desc, category_id: catId })}
          className="bg-blue-600 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors whitespace-nowrap"
        >
          Onayla
        </button>
      </div>
    </div>
  )
}
