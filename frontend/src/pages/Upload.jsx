import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiClient } from '../services/apiClient'

export default function Upload() {
  const [status, setStatus] = useState('idle')
  const navigate = useNavigate()

  const handleFile = useCallback(async (file) => {
    if (!file?.name.endsWith('.pdf')) {
      alert('Lutfen PDF formatinda banka ekstresi yukleyin.')
      return
    }
    setStatus('uploading')
    try {
      const form = new FormData()
      form.append('file', file)

      const res = await apiClient.post('/pdf/upload', form, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      setStatus('processing')

      const poll = setInterval(async () => {
        try {
          const s = await apiClient.get(`/pdf/uploads/${res.data.upload_id}`)
          if (['completed','needs_review','failed'].includes(s.data.status)) {
            clearInterval(poll)
            setStatus('done')
            setTimeout(() => navigate('/verify'), 800)
          }
        } catch (e) {
          clearInterval(poll)
          setStatus('idle')
          alert('Durum kontrol edilirken hata oluştu.')
        }
      }, 2000)
    } catch (err) {
      console.error(err)
      setStatus('idle')
      alert('Yükleme sırasında bir hata oluştu. Backend çalışıyor mu?')
    }
  }, [navigate])

  const labels = {
    idle:       'PDF\'i surukle birak veya tikla',
    uploading:  'Yukleniyor...',
    processing: 'Aliyda analiz ediyor...',
    done:       'Tamamlandi! Yonlendiriliyor...',
  }

  return (
    <div className="max-w-xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-2">Ekstreni Yukle</h1>
      <p className="text-gray-500 mb-6">PDF formatinda banka ekstreni yukle, Aliyda analiz etsin.</p>
      <div
        className="border-2 border-dashed border-blue-300 rounded-2xl p-16 text-center cursor-pointer hover:bg-blue-50 transition-colors"
        onDrop={(e) => { e.preventDefault(); handleFile(e.dataTransfer.files[0]) }}
        onDragOver={(e) => e.preventDefault()}
        onClick={() => document.getElementById('fi').click()}
      >
        <p className={`text-lg ${status !== 'idle' ? 'text-blue-500 animate-pulse' : 'text-gray-400'}`}>
          {labels[status]}
        </p>
        <input id="fi" type="file" accept=".pdf" className="hidden"
          onChange={(e) => handleFile(e.target.files[0])}/>
      </div>
      <p className="text-xs text-gray-400 text-center mt-4">Maksimum 10MB - Yalnizca PDF</p>
    </div>
  )
}
