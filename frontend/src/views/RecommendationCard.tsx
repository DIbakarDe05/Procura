import React, { useState } from 'react'
import { RecommendationItem, api } from '@/api/client'
import { useTranslation } from '@/i18n/LanguageContext'
import { StatusBadge } from './StatusBadge'

interface RecommendationCardProps {
  recommendation: RecommendationItem
  index?: number
}

function confidenceLabel(score: number | null | undefined): { text: string; cls: string } {
  if (score == null) return { text: 'N/A', cls: 'text-gray-400' }
  const val = score > 1 ? score : score * 100
  if (val >= 80) return { text: 'High', cls: 'text-green-700' }
  if (val >= 50) return { text: 'Medium', cls: 'text-amber-600' }
  return { text: 'Low', cls: 'text-red-600' }
}

function formatPct(score: number | null | undefined): string {
  if (score == null) return 'N/A'
  const val = score > 1 ? score : score * 100
  return `${Math.round(val)}%`
}

export const RecommendationCard: React.FC<RecommendationCardProps> = ({ recommendation, index }) => {
  const { t } = useTranslation()
  const [expanded, setExpanded] = useState(false)
  const [status, setStatus] = useState(recommendation.status)
  const [actionLoading, setActionLoading] = useState(false)

  const rec = recommendation
  const conf = confidenceLabel(rec.confidence_score)

  const coverageStatusDot = (stat: string): string => {
    switch (stat) {
      case 'covered': return 'bg-green-500'
      case 'partial': return 'bg-amber-500'
      case 'missing': return 'bg-red-500'
      default: return 'bg-gray-300'
    }
  }

  const coverageStatusLabel = (stat: string): string => {
    switch (stat) {
      case 'covered': return t.covCovered
      case 'partial': return t.covPartial
      case 'missing': return t.covMissing
      case 'not_applicable': return t.covNA
      default: return stat
    }
  }

  const handleAction = async (action: 'accept' | 'reject' | 'review') => {
    setActionLoading(true)
    try {
      let res
      if (action === 'accept') {
        res = await api.acceptRecommendation(rec.id)
      } else if (action === 'reject') {
        res = await api.rejectRecommendation(rec.id)
      } else {
        res = await api.reviewRecommendation(rec.id)
      }
      setStatus(res.status)
    } catch (err) {
      console.error('Action failed:', err)
    }
    setActionLoading(false)
  }

  return (
    <div className="card p-0 overflow-hidden animate-fade-in">
      {/* ── Requirement Header ────────────────────────── */}
      <div className="bg-navy-50 px-5 py-3 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            {index && (
              <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                {t.recommendationNum} #{String(index).padStart(2, '0')}
              </span>
            )}
          </div>
          <StatusBadge status={status} />
        </div>
      </div>

      <div className="p-5 space-y-4">
        {/* ── Standard Info ─────────────────────────────── */}
        <div>
          <div className="text-xs text-gray-500 font-medium mb-1">{t.recommendedLabel}</div>
          <h3 className="text-base font-bold text-navy-800">
            {rec.standard_number}
          </h3>
          <p className="text-sm text-gray-600 mt-0.5">{rec.standard_title}</p>
        </div>

        {/* ── Scores: Relevance % + Confidence ─────────── */}
        <div className="flex items-center gap-6 py-3 px-4 bg-gray-50 rounded-md">
          <div>
            <span className="text-xs text-gray-500 font-medium">{t.relevance}: </span>
            <span className={`text-sm font-bold ${
              (rec.relevance_score || 0) >= 80 ? 'text-green-700' :
              (rec.relevance_score || 0) >= 50 ? 'text-amber-600' : 'text-red-600'
            }`}>
              {formatPct(rec.relevance_score)}
            </span>
          </div>
          <div>
            <span className="text-xs text-gray-500 font-medium">{t.confidence}: </span>
            <span className={`text-sm font-bold ${conf.cls}`}>
              {conf.text}
            </span>
          </div>
          {rec.compliance_score != null && (
            <div>
              <span className="text-xs text-gray-500 font-medium">{t.compliance}: </span>
              <span className={`text-sm font-bold ${
                (rec.compliance_score > 1 ? rec.compliance_score : rec.compliance_score * 100) >= 80 ? 'text-green-700' :
                (rec.compliance_score > 1 ? rec.compliance_score : rec.compliance_score * 100) >= 50 ? 'text-amber-600' : 'text-red-600'
              }`}>
                {formatPct(rec.compliance_score)}
              </span>
            </div>
          )}
        </div>

        {/* ── Why? (Reasoning) ─────────────────────────── */}
        {rec.reasoning && (
          <div>
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">{t.whyLabel}</div>
            <p className="text-sm text-gray-700 leading-relaxed">{rec.reasoning}</p>
          </div>
        )}

        {/* ── Related Standards (always visible) ──────── */}
        {rec.related_standards && rec.related_standards.length > 0 && (
          <div>
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">{t.relatedStandards}</div>
            <ul className="space-y-1">
              {rec.related_standards.map((rs, i) => (
                <li key={i} className="flex items-center gap-2 text-sm">
                  <span className="text-gray-400">•</span>
                  <span className="badge bg-gray-100 text-gray-600 text-[10px]">
                    {rs.reference_type.replace(/_/g, ' ')}
                  </span>
                  <span className="font-medium text-navy-700">{rs.standard_number}</span>
                  {rs.title && <span className="text-gray-500">— {rs.title}</span>}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* ── Officer Actions ──────────────────────────── */}
        <div className="flex items-center gap-2 pt-3 border-t border-gray-100">
          <button
            onClick={() => handleAction('accept')}
            disabled={actionLoading || status === 'accepted'}
            className={`btn-outline text-xs ${status === 'accepted' ? 'bg-green-50 border-green-300 text-green-700' : ''}`}
          >
            {t.btnAccept}
          </button>
          <button
            onClick={() => handleAction('reject')}
            disabled={actionLoading || status === 'rejected'}
            className={`btn-outline text-xs ${status === 'rejected' ? 'bg-red-50 border-red-300 text-red-700' : ''}`}
          >
            {t.btnReject}
          </button>
          <button
            onClick={() => setExpanded(!expanded)}
            className="btn-outline text-xs ml-auto"
          >
            {expanded ? t.btnHideDetails : t.btnViewDetails}
          </button>
        </div>

        {/* ── Expanded Details ─────────────────────────── */}
        {expanded && (
          <div className="space-y-5 border-t border-gray-100 pt-4 animate-fade-in">
            {/* Coverage */}
            {rec.coverage && rec.coverage.length > 0 && (
              <div>
                <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">{t.coverageTitle}</div>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs text-gray-500 border-b border-gray-100">
                      <th className="pb-2 font-medium">{t.colCategory}</th>
                      <th className="pb-2 font-medium">{t.colStatus}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rec.coverage.map((c, i) => (
                      <tr key={i} className="border-b border-gray-50">
                        <td className="py-2 text-gray-700">{c.category}</td>
                        <td className="py-2">
                          <span className="flex items-center gap-2">
                            <span className={`w-2 h-2 rounded-full ${coverageStatusDot(c.status)}`} />
                            <span className="text-gray-600">{coverageStatusLabel(c.status)}</span>
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Gaps */}
            {rec.gaps && rec.gaps.length > 0 && (
              <div>
                <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">{t.gapsTitle}</div>
                <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                  {rec.gaps.map((gap, i) => (
                    <li key={i}>{gap}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Version Info */}
            {rec.version_info && (
              <div>
                <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">{t.versionInfoTitle}</div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
                  <div>
                    <span className="text-gray-500 text-xs">{t.edition}</span>
                    <div className="font-medium text-gray-800">{rec.version_info.edition || '—'}</div>
                  </div>
                  <div>
                    <span className="text-gray-500 text-xs">{t.status}</span>
                    <div className="font-medium text-gray-800">{rec.version_info.status || '—'}</div>
                  </div>
                  <div>
                    <span className="text-gray-500 text-xs">{t.current}</span>
                    <div className="font-medium">
                      {rec.version_info.is_current ? (
                        <span className="text-green-700">{t.yes}</span>
                      ) : (
                        <span className="text-red-600">{t.no}</span>
                      )}
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-500 text-xs">{t.amendments}</span>
                    <div className="font-medium text-gray-800">
                      {rec.version_info.amendments && rec.version_info.amendments.length > 0
                        ? rec.version_info.amendments.map((a: any) => a.amendment || a).join(', ')
                        : t.none}
                    </div>
                  </div>
                </div>
                {rec.version_info.note && (
                  <p className="mt-2 text-xs text-gray-500">{rec.version_info.note}</p>
                )}
              </div>
            )}

            {/* Certification */}
            {rec.certification_info && (
              <div>
                <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">{t.certificationTitle}</div>
                <div className="flex items-start gap-4 text-sm">
                  <div>
                    <span className="text-gray-500 text-xs">{t.required}</span>
                    <div className="font-medium mt-0.5">
                      {rec.certification_info.certification_required ? (
                        <span className="badge bg-red-100 text-red-800">{t.required}</span>
                      ) : (
                        <span className="badge bg-green-100 text-green-800">{t.notRequired}</span>
                      )}
                    </div>
                  </div>
                  {rec.certification_info.certification_details && (
                    <div className="flex-1">
                      <span className="text-gray-500 text-xs">{t.details}</span>
                      <div className="text-gray-700 mt-0.5">{rec.certification_info.certification_details}</div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
