import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { supabase } from '../services/supabaseClient'
import { LayoutDashboard, FileUp, CheckSquare, Target, LogOut, Wallet } from 'lucide-react'

export default function Layout() {
  const { user } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await supabase.auth.signOut()
    navigate('/login')
  }

  const menu = [
    { path: '/', name: 'Dashboard', icon: LayoutDashboard },
    { path: '/upload', name: 'Ekstre Yükle', icon: FileUp },
    { path: '/verify', name: 'Doğrulama', icon: CheckSquare },
    { path: '/goals', name: 'Hedefler', icon: Target },
  ]

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col hidden md:flex">
        <div className="p-6 flex items-center gap-3">
          <div className="bg-blue-600 p-2 rounded-lg">
            <Wallet className="text-white w-6 h-6" />
          </div>
          <span className="text-white font-bold text-xl tracking-tight">Aliyda</span>
        </div>
        
        <nav className="flex-1 px-4 space-y-2 mt-4">
          {menu.map(item => {
            const Icon = item.icon
            const active = location.pathname === item.path
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                  active 
                    ? 'bg-blue-600/10 text-blue-400 font-medium' 
                    : 'hover:bg-slate-800 hover:text-white'
                }`}
              >
                <Icon className={`w-5 h-5 ${active ? 'text-blue-400' : 'text-slate-400'}`} />
                {item.name}
              </Link>
            )
          })}
        </nav>

        <div className="p-4 border-t border-slate-800">
          <div className="px-4 py-3 mb-2 rounded-xl bg-slate-800/50">
            <p className="text-xs text-slate-400">Giriş yapıldı</p>
            <p className="text-sm text-white font-medium truncate">{user?.email}</p>
          </div>
          <button 
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-red-400 hover:bg-red-500/10 hover:text-red-300 transition-all"
          >
            <LogOut className="w-5 h-5" />
            Çıkış Yap
          </button>
        </div>
      </aside>

      {/* Mobile Header (simplified) */}
      <div className="md:hidden fixed top-0 left-0 right-0 bg-slate-900 text-white p-4 flex justify-between items-center z-50">
        <div className="flex items-center gap-2">
          <Wallet className="w-6 h-6 text-blue-400" />
          <span className="font-bold text-lg">Aliyda</span>
        </div>
        <button onClick={handleLogout} className="text-slate-400 hover:text-white">
          <LogOut className="w-5 h-5" />
        </button>
      </div>

      {/* Mobile Navigation Bottom Bar */}
      <div className="md:hidden fixed bottom-0 left-0 right-0 bg-slate-900 text-slate-400 flex justify-around p-3 z-50 pb-safe">
        {menu.map(item => {
          const Icon = item.icon
          const active = location.pathname === item.path
          return (
            <Link key={item.path} to={item.path} className={`p-2 rounded-lg flex flex-col items-center gap-1 ${active ? 'text-blue-400' : 'hover:text-white'}`}>
              <Icon className="w-6 h-6" />
              <span className="text-[10px]">{item.name}</span>
            </Link>
          )
        })}
      </div>

      {/* Main Content */}
      <main className="flex-1 overflow-auto bg-slate-50 relative pt-16 md:pt-0 pb-20 md:pb-0">
        <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 pointer-events-none"></div>
        <div className="relative z-10 p-4 md:p-8">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
