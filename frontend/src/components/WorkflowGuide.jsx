import { Link } from 'react-router-dom'
import {
  ArrowRight, CheckCircle2, FileUp, LayoutDashboard,
  ListChecks, MessageSquare, ShieldCheck,
} from 'lucide-react'

const STEPS = [
  {
    title: 'PDF yükle',
    body: 'Banka ekstresini yükle; Aliyda işlem taslaklarını çıkarsın.',
    to: '/upload',
    cta: 'PDF Yükle',
    icon: FileUp,
  },
  {
    title: 'Doğrula',
    body: 'Taslak işlemleri incele, düzenle, onayla veya reddet.',
    to: '/verify',
    cta: 'Doğrulamaya Git',
    icon: ShieldCheck,
  },
  {
    title: 'İşlemleri gör',
    body: 'Onaylanan kayıtlar burada resmi finans verin olur.',
    to: '/transactions',
    cta: 'İşlemleri Aç',
    icon: ListChecks,
  },
  {
    title: 'Yorum al',
    body: 'Dashboard özetini incele, detaylı soruları chatbot’a sor.',
    to: '/chat',
    cta: 'Chatbot’a Sor',
    icon: MessageSquare,
  },
]

export default function WorkflowGuide({ active = '', compact = false }) {
  return (
    <section className={`glass-panel rounded-2xl ${compact ? 'p-4' : 'p-5'} mb-6`}>
      <div className="flex items-start justify-between gap-4 mb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <div className="p-1.5 rounded-lg bg-violet-500/20 text-violet-300">
              <LayoutDashboard size={15} />
            </div>
            <h2 className="text-white text-sm font-semibold tracking-wide uppercase">Aliyda Akışı</h2>
          </div>
          <p className="text-gray-400 text-xs leading-relaxed">
            Veriler önce doğrulanır; dashboard ve chatbot yalnızca onaylanmış işlemlerle çalışır.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
        {STEPS.map((step, index) => {
          const Icon = step.icon
          const isActive = active === step.to
          return (
            <Link
              key={step.to}
              to={step.to}
              className={`group rounded-xl border px-4 py-3 transition-all min-h-[128px] flex flex-col ${
                isActive
                  ? 'border-violet-400/60 bg-violet-500/15 shadow-[0_0_22px_rgba(139,92,246,0.18)]'
                  : 'border-white/5 bg-black/15 hover:border-violet-400/40 hover:bg-white/[0.04]'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                  isActive ? 'bg-violet-500 text-white' : 'bg-gray-800 text-gray-300 group-hover:text-violet-300'
                }`}>
                  <Icon size={16} />
                </div>
                <span className="text-[11px] text-gray-500 font-semibold">0{index + 1}</span>
              </div>
              <h3 className="text-sm text-white font-semibold mb-1">{step.title}</h3>
              <p className="text-xs text-gray-400 leading-relaxed flex-1">{step.body}</p>
              <div className="flex items-center gap-1 text-xs text-violet-300 font-medium mt-3">
                {isActive ? (
                  <>
                    <CheckCircle2 size={13} />
                    Şu an buradasın
                  </>
                ) : (
                  <>
                    {step.cta}
                    <ArrowRight size={13} className="group-hover:translate-x-0.5 transition-transform" />
                  </>
                )}
              </div>
            </Link>
          )
        })}
      </div>
    </section>
  )
}
