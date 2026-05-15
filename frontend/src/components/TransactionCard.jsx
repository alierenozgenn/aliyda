import { useState } from 'react'

export function TransactionCard({ transaction, onVerify }) {
  const [desc, setDesc] = useState(transaction.description || '')
  
  return (
    <div className="border rounded-xl p-4 bg-white flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
      <div className="flex-1 w-full">
        <input 
          className="border rounded p-2 w-full text-sm font-medium mb-2" 
          value={desc} 
          onChange={e => setDesc(e.target.value)}
        />
        <div className="flex items-center gap-3 text-sm text-gray-500">
          <span>{transaction.date}</span>
          <span className={`font-bold ${transaction.direction === 'income' ? 'text-green-600' : 'text-red-600'}`}>
            {transaction.amount} TL
          </span>
          <span className="text-xs px-2 py-1 bg-gray-100 rounded-full border">
            Güven: %{Math.round(transaction.confidence * 100)}
          </span>
          <span className="text-xs px-2 py-1 bg-blue-50 text-blue-600 rounded-full border border-blue-200">
            {transaction.categories?.name || transaction.estimated_category || 'Kategori Yok'}
          </span>
        </div>
      </div>
      <div>
        <button 
          onClick={() => onVerify({ description: desc })}
          className="bg-blue-600 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
        >
          Onayla
        </button>
      </div>
    </div>
  )
}
