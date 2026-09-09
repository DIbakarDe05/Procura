import React, { useState, useEffect, useRef } from 'react'
import { useTranslation } from '@/i18n/LanguageContext'
import { Language } from '@/i18n/types'

interface HeaderProps {
  currentView: 'landing' | 'query' | 'tender'
  onNavigate: (view: 'landing' | 'query' | 'tender') => void
}

export const Header: React.FC<HeaderProps> = ({ currentView, onNavigate }) => {
  const [langOpen, setLangOpen] = useState(false)
  const langRef = useRef<HTMLDivElement>(null)
  const { language, setLanguage, t, currentLanguage, supportedLanguages } = useTranslation()


  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (langRef.current && !langRef.current.contains(event.target as Node)) {
        setLangOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const navItems = [
    { key: 'landing' as const, label: t.navHome },
    { key: 'query' as const, label: t.navQuery },
    { key: 'tender' as const, label: t.navTender },
  ]

  return (
    <header className="bg-white border-b border-gray-200 shadow-sm">
      {/* Saffron accent line */}
      <div className="h-1 bg-saffron-500" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div
            className="flex items-center gap-3 cursor-pointer"
            onClick={() => onNavigate('landing')}
          >
            <div className="flex items-center justify-center w-9 h-9 rounded-md bg-navy-700">
              <svg
                className="w-5 h-5 text-white"
                fill="none"
                stroke="currentColor"
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
                viewBox="0 0 24 24"
              >
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              </svg>
            </div>
            <div>
              <div className="text-lg font-bold text-navy-700 tracking-tight leading-tight">
                {t.portalTitle}
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="hidden sm:flex items-center gap-1">
            {navItems.map((item) => (
              <button
                key={item.key}
                onClick={() => onNavigate(item.key)}
                className={`px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                  currentView === item.key
                    ? 'bg-navy-700 text-white'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                }`}
              >
                {item.label}
              </button>
            ))}
          </nav>

          {/* Right Actions: Language Switcher */}
          <div className="flex items-center gap-3">
            {/* Language Switcher Dropdown */}
            <div className="relative" ref={langRef}>
              <button
                onClick={() => setLangOpen(!langOpen)}
                className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium text-navy-800 bg-gray-50 hover:bg-gray-100 rounded-md border border-gray-200 transition-colors"
                title={t.langSelect}
              >
                <svg
                  className="w-3.5 h-3.5 text-navy-600"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth={2}
                  viewBox="0 0 24 24"
                >
                  <circle cx="12" cy="12" r="10" />
                  <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
                </svg>
                <span>{currentLanguage.nativeName}</span>
                <svg
                  className={`w-3 h-3 text-gray-500 transition-transform ${langOpen ? 'rotate-180' : ''}`}
                  fill="none"
                  stroke="currentColor"
                  strokeWidth={2}
                  viewBox="0 0 24 24"
                >
                  <polyline points="6 9 12 15 18 9" />
                </svg>
              </button>

              {langOpen && (
                <div className="absolute right-0 mt-1 w-36 bg-white border border-gray-200 rounded-md shadow-lg py-1 z-50 animate-fade-in">
                  <div className="px-3 py-1 text-[10px] font-semibold text-gray-400 uppercase tracking-wider">
                    {t.langSelect}
                  </div>
                  {supportedLanguages.map((opt) => (
                    <button
                      key={opt.code}
                      onClick={() => {
                        setLanguage(opt.code as Language)
                        setLangOpen(false)
                      }}
                      className={`w-full text-left px-3 py-1.5 text-xs flex items-center justify-between transition-colors ${
                        language === opt.code
                          ? 'bg-navy-50 font-semibold text-navy-800'
                          : 'text-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      <span>{opt.nativeName}</span>
                      <span className="text-[10px] text-gray-400">{opt.label}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}
