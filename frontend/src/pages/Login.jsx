import { useState } from 'react'
import { supabase } from '../services/supabaseClient'
import { useNavigate } from 'react-router-dom'
import { Wallet, LogIn, Lock, Mail, ArrowRight } from 'lucide-react'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [isRegister, setIsRegister] = useState(false)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  const handleAuth = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    
    try {
      if (isRegister) {
        const { error } = await supabase.auth.signUp({ email, password })
        if (error) throw error
        alert('Kayıt başarılı! Lütfen giriş yapın.')
        setIsRegister(false)
      } else {
        const { error } = await supabase.auth.signInWithPassword({ email, password })
        if (error) throw error
        navigate('/')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 p-4">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-[30%] -left-[10%] w-[70%] h-[70%] rounded-full bg-blue-500/20 blur-[120px]" />
        <div className="absolute -bottom-[30%] -right-[10%] w-[70%] h-[70%] rounded-full bg-purple-500/20 blur-[120px]" />
      </div>

      <div className="w-full max-w-md bg-white/10 backdrop-blur-xl border border-white/20 rounded-3xl p-8 shadow-2xl relative z-10">
        <div className="text-center mb-8">
          <div className="bg-blue-500/20 w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4 border border-blue-400/30">
            <Wallet className="text-blue-400 w-8 h-8" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">Aliyda</h1>
          <p className="text-blue-200/80">Kişisel Finans Asistanınız</p>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/50 text-red-200 p-3 rounded-lg text-sm mb-6 text-center">
            {error}
          </div>
        )}

        <form onSubmit={handleAuth} className="space-y-4">
          <div>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-blue-200/50" />
              <input
                type="email"
                placeholder="E-posta Adresi"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-slate-900/50 border border-white/10 rounded-xl py-3 pl-10 pr-4 text-white placeholder:text-blue-200/50 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent transition-all"
                required
              />
            </div>
          </div>
          
          <div>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-blue-200/50" />
              <input
                type="password"
                placeholder="Şifre"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-slate-900/50 border border-white/10 rounded-xl py-3 pl-10 pr-4 text-white placeholder:text-blue-200/50 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent transition-all"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-500 text-white rounded-xl py-3 px-4 font-medium transition-all flex items-center justify-center group disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'İşleniyor...' : (isRegister ? 'Kayıt Ol' : 'Giriş Yap')}
            {!loading && <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />}
          </button>
        </form>

        <div className="mt-6 text-center">
          <button
            onClick={() => setIsRegister(!isRegister)}
            className="text-sm text-blue-300 hover:text-white transition-colors"
          >
            {isRegister ? 'Zaten hesabınız var mı? Giriş yapın' : 'Hesabınız yok mu? Kayıt olun'}
          </button>
        </div>
      </div>
    </div>
  )
}
