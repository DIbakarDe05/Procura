import React from 'react'
import { useTranslation } from '@/i18n/LanguageContext'

interface LandingPageProps {
  onNavigate: (view: 'query' | 'tender') => void
}

export const LandingPage: React.FC<LandingPageProps> = ({ onNavigate }) => {
  const { t } = useTranslation()

  return (
    <div className="animate-fade-in space-y-12">
      {/* Hero */}
      <div className="text-center py-8 sm:py-12">
        <span className="badge bg-saffron-50 text-saffron-700 border border-saffron-200 mb-4 inline-block">
          {t.heroBadge}
        </span>
        <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mt-3 leading-tight tracking-tight">
          {t.heroTitle}
        </h1>
        <p className="mt-4 text-gray-600 max-w-3xl mx-auto leading-relaxed text-sm sm:text-base">
          {t.heroSubtitle}
        </p>
      </div>

      {/* Two Main Option Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto">
        {/* Tender PDF Card */}
        <div
          className="card p-6 sm:p-8 cursor-pointer hover:shadow-md hover:border-navy-200 transition-all group border-t-4 border-t-navy-700"
          onClick={() => onNavigate('tender')}
        >
          <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-navy-50 text-navy-700 mb-4 group-hover:bg-navy-100 transition-colors">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-gray-900">{t.cardTenderTitle}</h2>
          <p className="mt-2 text-sm text-gray-600 leading-relaxed">
            {t.cardTenderDesc}
          </p>
          <div className="mt-5">
            <span className="btn-primary text-sm inline-flex items-center gap-1.5">
              {t.cardTenderTitle} →
            </span>
          </div>
        </div>

        {/* Query Card */}
        <div
          className="card p-6 sm:p-8 cursor-pointer hover:shadow-md hover:border-navy-200 transition-all group border-t-4 border-t-saffron-500"
          onClick={() => onNavigate('query')}
        >
          <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-navy-50 text-navy-700 mb-4 group-hover:bg-navy-100 transition-colors">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-gray-900">{t.cardQueryTitle}</h2>
          <p className="mt-2 text-sm text-gray-600 leading-relaxed">
            {t.cardQueryDesc}
          </p>
          <div className="mt-5">
            <span className="btn-primary text-sm inline-flex items-center gap-1.5">
              {t.cardQueryTitle} →
            </span>
          </div>
        </div>
      </div>

      {/* Enterprise Feature Highlights */}
      <div className="max-w-4xl mx-auto pt-6">
        <h3 className="text-lg font-bold text-gray-900 mb-6 text-center">{t.featuresTitle}</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="p-4 bg-white rounded-lg border border-gray-200">
            <div className="text-sm font-bold text-navy-800 mb-1 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-navy-600" />
              {t.featZeroHallucination}
            </div>
            <p className="text-xs text-gray-600 leading-relaxed">{t.featZeroHallucinationDesc}</p>
          </div>

          <div className="p-4 bg-white rounded-lg border border-gray-200">
            <div className="text-sm font-bold text-navy-800 mb-1 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-saffron-500" />
              {t.featGapAnalysis}
            </div>
            <p className="text-xs text-gray-600 leading-relaxed">{t.featGapAnalysisDesc}</p>
          </div>

          <div className="p-4 bg-white rounded-lg border border-gray-200">
            <div className="text-sm font-bold text-navy-800 mb-1 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green-600" />
              {t.featVersionCheck}
            </div>
            <p className="text-xs text-gray-600 leading-relaxed">{t.featVersionCheckDesc}</p>
          </div>

          <div className="p-4 bg-white rounded-lg border border-gray-200">
            <div className="text-sm font-bold text-navy-800 mb-1 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-purple-600" />
              {t.featOfficerAudit}
            </div>
            <p className="text-xs text-gray-600 leading-relaxed">{t.featOfficerAuditDesc}</p>
          </div>
        </div>
      </div>

      {/* Metric Indicators */}
      <div className="flex flex-wrap items-center justify-center gap-4 sm:gap-8 text-xs text-gray-500 pt-4">
        <span className="flex items-center gap-1.5 font-medium">
          <span className="w-2 h-2 rounded-full bg-green-500" />
          {t.statStandards}
        </span>
        <span>•</span>
        <span className="font-medium">{t.statAccuracy}</span>
        <span>•</span>
        <span className="font-medium">{t.statTurnaround}</span>
        <span>•</span>
        <span className="font-medium">{t.statAlignment}</span>
      </div>
    </div>
  )
}
