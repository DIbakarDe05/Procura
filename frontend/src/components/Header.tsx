import React, { useState, useEffect } from 'react'
import { FileText, Sparkles, Database, ShieldCheck, Activity, Info, X } from 'lucide-react'
import { api } from '@/api/client'

interface HeaderProps {
  activeTab: 'tender' | 'query'
  onTabChange: (tab: 'tender' | 'query') => void
}

export const Header: React.FC<HeaderProps> = ({ activeTab, onTabChange }) => {
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null)
  const [showStatsModal, setShowStatsModal] = useState(false)
  const [stats, setStats] = useState<{
    total_standards: number
    total_references: number
    embedding_dimension: number
    embedding_model: string
  } | null>(null)

  useEffect(() => {
    const check = async () => {
      try {
        const res = await api.checkHealth()
        setIsHealthy(res.status === 'healthy')
      } catch {
        setIsHealthy(false)
      }
    }
    check()
    const interval = setInterval(check, 10000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (showStatsModal && !stats) {
      api.getStandardsStats().then(setStats).catch(() => {})
    }
  }, [showStatsModal, stats])

  return (
    <>
      <header className="sticky top-0 z-40 w-full border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3.5 sm:px-6 lg:px-8">
          {/* Logo & Problem Statement Badge */}
          <div className="flex items-center gap-3.5">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-indigo-700 shadow-lg shadow-indigo-500/25 ring-1 ring-indigo-400/30">
              <ShieldCheck className="h-6 w-6 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-display text-xl font-extrabold tracking-tight text-white">
                  PROCURA
                </span>
                <span className="rounded-full bg-indigo-500/10 px-2 py-0.5 text-[11px] font-semibold text-indigo-400 ring-1 ring-inset ring-indigo-500/20">
                  SIH 26108
                </span>
              </div>
              <p className="text-xs text-slate-400">
                BIS Indian Standards Procurement Engine
              </p>
            </div>
          </div>

          {/* Mode Switcher */}
          <div className="flex items-center rounded-xl bg-slate-900/90 p-1 ring-1 ring-slate-800">
            <button
              onClick={() => onTabChange('tender')}
              className={`flex items-center gap-2 rounded-lg px-3.5 py-1.5 text-sm font-medium transition-all ${
                activeTab === 'tender'
                  ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <FileText className="h-4 w-4" />
              <span>Tender Analyzer</span>
            </button>
            <button
              onClick={() => onTabChange('query')}
              className={`flex items-center gap-2 rounded-lg px-3.5 py-1.5 text-sm font-medium transition-all ${
                activeTab === 'query'
                  ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Sparkles className="h-4 w-4" />
              <span>Query Studio</span>
            </button>
          </div>

          {/* Right Action & Status */}
          <div className="flex items-center gap-3">
            {/* Database & Engine Stats Button */}
            <button
              onClick={() => setShowStatsModal(true)}
              className="flex items-center gap-1.5 rounded-lg border border-slate-800 bg-slate-900/60 px-2.5 py-1.5 text-xs font-medium text-slate-300 hover:bg-slate-800/80 hover:text-white transition-colors"
            >
              <Database className="h-3.5 w-3.5 text-indigo-400" />
              <span className="hidden sm:inline">BIS Knowledge Base</span>
            </button>

            {/* Health Indicator */}
            <div className="flex items-center gap-2 rounded-full border border-slate-800/80 bg-slate-900/80 px-2.5 py-1 text-xs">
              <span className="relative flex h-2 w-2">
                <span
                  className={`absolute inline-flex h-full w-full animate-ping rounded-full opacity-75 ${
                    isHealthy ? 'bg-emerald-400' : 'bg-rose-400'
                  }`}
                />
                <span
                  className={`relative inline-flex h-2 w-2 rounded-full ${
                    isHealthy ? 'bg-emerald-500' : 'bg-rose-500'
                  }`}
                />
              </span>
              <span className="font-medium text-slate-300">
                {isHealthy === null ? 'Connecting...' : isHealthy ? 'Engine Active' : 'Offline'}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Standards Knowledge Base Modal */}
      {showStatsModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="glass-panel w-full max-w-lg rounded-2xl border border-slate-700/70 p-6 shadow-2xl animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center gap-2.5">
                <Database className="h-5 w-5 text-indigo-400" />
                <h3 className="font-display text-lg font-bold text-white">
                  Verified BIS Standards Knowledge Base
                </h3>
              </div>
              <button
                onClick={() => setShowStatsModal(false)}
                className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="mt-5 space-y-4 text-sm text-slate-300">
              <p className="text-slate-400 leading-relaxed">
                Procura operates on a strict zero-hallucination policy. All standard recommendations are verified against our authoritative database rather than generated ungrounded by the LLM.
              </p>

              <div className="grid grid-cols-2 gap-3 pt-1">
                <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3.5">
                  <div className="text-xs font-medium text-slate-400">Indexed BIS Standards</div>
                  <div className="mt-1 font-display text-2xl font-bold text-white">
                    {stats ? `${stats.total_standards} Verified` : '27 Verified'}
                  </div>
                  <div className="text-[11px] text-emerald-400 mt-0.5">IS 9999, IS 9079, IS 9137...</div>
                </div>
                <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3.5">
                  <div className="text-xs font-medium text-slate-400">Normative Graph Links</div>
                  <div className="mt-1 font-display text-2xl font-bold text-indigo-400">
                    {stats ? `${stats.total_references} References` : '18 References'}
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">Test, Safety, Material links</div>
                </div>
                <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3.5">
                  <div className="text-xs font-medium text-slate-400">Vector Embeddings</div>
                  <div className="mt-1 font-display text-xl font-bold text-cyan-400">
                    {stats ? `${stats.embedding_dimension}-dim` : '3072-dim'}
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">Gemini-Embedding-2 Active</div>
                </div>
                <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3.5">
                  <div className="text-xs font-medium text-slate-400">OCR Engine</div>
                  <div className="mt-1 font-display text-xl font-bold text-emerald-400">Tesseract v5.5.3</div>
                  <div className="text-[11px] text-slate-400 mt-0.5">Auto-fallback for scans</div>
                </div>
              </div>

              <div className="rounded-xl border border-indigo-500/20 bg-indigo-500/10 p-3 text-xs text-indigo-200">
                <span className="font-semibold text-indigo-300">Reasoning Core:</span> Google Gemini 3.1 Flash-Lite evaluates top retrieved candidates against your exact specifications.
              </div>
            </div>

            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setShowStatsModal(false)}
                className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
