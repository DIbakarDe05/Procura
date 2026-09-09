import React from 'react'
import { useTranslation } from '@/i18n/LanguageContext'

export const Footer: React.FC = () => {
  const { t } = useTranslation()

  return (
    <footer className="bg-white border-t border-gray-200 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center justify-center text-xs text-gray-500">
          <span className="font-semibold text-navy-700">{t.portalTitle}</span>
        </div>
      </div>
    </footer>
  )
}
