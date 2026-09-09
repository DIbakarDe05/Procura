import React, { useState, useRef, useCallback } from 'react'
import { api, ReportResponse, QueryDetailResponse } from '@/api/client'
import { useTranslation } from '@/i18n/LanguageContext'
import { RecommendationCard } from './RecommendationCard'

interface QueryWorkflowProps {
  onBack: () => void
}

export const QueryWorkflow: React.FC<QueryWorkflowProps> = ({ onBack }) => {
  const { t } = useTranslation()
  const [queryText, setQueryText] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [statusMessage, setStatusMessage] = useState('')
  const [queryDetails, setQueryDetails] = useState<QueryDetailResponse | null>(null)
  const [report, setReport] = useState<ReportResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const cleanup = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }, [])

  const handleSubmit = async (textToSubmit?: string) => {
    const text = textToSubmit || queryText
    if (!text.trim()) return

    cleanup()
    setIsSubmitting(true)
    setError(null)
    setReport(null)
    setQueryDetails(null)
    setStatusMessage(t.btnAnalyzing)

    try {
      const submitRes = await api.submitQuery(text)
      const queryId = submitRes.id

      setStatusMessage(t.btnAnalyzing)

      let attempts = 0
      const maxAttempts = 150  // 5 minutes (150 * 2000ms)

      pollRef.current = setInterval(async () => {
        attempts++
        try {
          const details = await api.getQueryDetails(queryId)
          setQueryDetails(details)

          if (details.status === 'received') {
            setStatusMessage(t.btnAnalyzing)
          } else if (details.status === 'processing') {
            setStatusMessage(t.stageLabels.generating_embeddings || 'Extracting requirements...')
          } else if (details.status === 'analyzing') {
            setStatusMessage(t.stageLabels.analyzing_top_k || 'Evaluating candidate BIS standards...')
          } else if (details.status === 'completed') {
            cleanup()
            setStatusMessage('')
            const rep = await api.getQueryReport(queryId)
            setReport(rep)
            setIsSubmitting(false)
          } else if (details.status === 'failed') {
            cleanup()
            setError(t.stageLabels.failed || 'Analysis failed. Please try again.')
            setIsSubmitting(false)
          }

          if (attempts >= maxAttempts) {
            cleanup()
            setError('Analysis timed out. The server may still be processing.')
            setIsSubmitting(false)
          }
        } catch (pollErr) {
          console.error('Polling error:', pollErr)
        }
      }, 2000)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
      setIsSubmitting(false)
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Back + Title */}
      <div>
        <button onClick={onBack} className="text-sm text-navy-700 hover:underline mb-2">
          {t.backToHome}
        </button>
        <h1 className="text-2xl font-bold text-gray-900">{t.queryTitle}</h1>
        <p className="text-sm text-gray-600 mt-1">
          {t.querySubtitle}
        </p>
      </div>

      {/* Input */}
      <div className="card p-5">
        <label htmlFor="query-input" className="block text-sm font-semibold text-gray-800 mb-2">
          {t.querySubtitle}
        </label>
        <textarea
          id="query-input"
          rows={4}
          value={queryText}
          onChange={(e) => setQueryText(e.target.value)}
          placeholder={t.queryPlaceholder}
          className="w-full rounded-md border border-gray-300 px-4 py-3 text-sm text-gray-900 placeholder-gray-400 focus:border-navy-700 focus:ring-1 focus:ring-navy-700 transition-colors"
        />
        <div className="flex items-center justify-between mt-3">
          <div className="text-xs text-gray-500">
            {queryText.length} {t.charCount}
          </div>
          <button
            onClick={() => handleSubmit()}
            disabled={isSubmitting || queryText.trim().length < 5}
            className="btn-primary"
          >
            {isSubmitting ? (
              <>
                <svg className="w-4 h-4 animate-spin-slow" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                {t.btnAnalyzing}
              </>
            ) : (
              t.btnRecommend
            )}
          </button>
        </div>
      </div>

      {/* Processing Status */}
      {isSubmitting && (
        <div className="card p-5 border-navy-200 bg-navy-50">
          <div className="flex items-center gap-3">
            <svg className="w-5 h-5 animate-spin-slow text-navy-700" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <div>
              <div className="text-sm font-semibold text-navy-800">{t.processingTitle}</div>
              <div className="text-xs text-navy-600 mt-0.5">{statusMessage}</div>
            </div>
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="card p-4 border-red-200 bg-red-50">
          <div className="flex items-center gap-2 text-sm text-red-800">
            <span className="font-semibold">Error:</span>
            <span>{error}</span>
          </div>
          <button
            onClick={() => { setError(null); handleSubmit() }}
            className="mt-2 text-xs font-medium text-red-700 hover:underline"
          >
            Retry
          </button>
        </div>
      )}

      {/* Extracted Requirements */}
      {queryDetails && queryDetails.requirements && queryDetails.requirements.length > 0 && (
        <div className="card p-5">
          <h2 className="section-title mb-3">
            {t.extractedReqs} ({queryDetails.requirements.length})
          </h2>
          <div className="space-y-2">
            {queryDetails.requirements.map((r, i) => (
              <div key={i} className="flex items-start gap-3 text-sm py-2 border-b border-gray-50 last:border-0">
                <span className="badge bg-navy-50 text-navy-700 shrink-0 mt-0.5">
                  {r.requirement_type}
                </span>
                <span className="text-gray-700">{r.requirement}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Compliance Note */}
      {report?.compliance_note && (
        <div className="card p-4 border-amber-200 bg-amber-50">
          <div className="text-sm">
            <span className="font-semibold text-amber-800">{t.genericQueryNote}: </span>
            <span className="text-amber-700">{report.compliance_note}</span>
          </div>
        </div>
      )}

      {/* Results */}
      {report && (
        <div className="space-y-4">
          {/* Summary Header */}
          {(() => {
            const displayRecs = (report.recommendations || []).slice(0, 4)
            const totalGaps = displayRecs.reduce((sum, r) => sum + (r.gaps?.length || 0), 0)
            const versionIssues = displayRecs.filter(
              r => r.version_info && !r.version_info.is_current
            ).length

            return (
              <>
                <div className="card p-6">
                  <h2 className="text-xl font-bold text-navy-800 mb-4 tracking-tight">
                    {t.standardsReview}
                  </h2>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="p-4 bg-navy-50 rounded-lg text-center">
                      <div className="text-2xl font-bold text-navy-800">
                        {report.total_requirements}
                      </div>
                      <div className="text-xs text-gray-600 mt-1 font-medium">
                        {t.reqsAnalyzed}
                      </div>
                    </div>
                    <div className="p-4 bg-green-50 rounded-lg text-center">
                      <div className="text-2xl font-bold text-green-700">
                        {displayRecs.length}
                      </div>
                      <div className="text-xs text-gray-600 mt-1 font-medium">
                        {t.topStdsRecommended}
                      </div>
                    </div>
                    <div className="p-4 bg-amber-50 rounded-lg text-center">
                      <div className="text-2xl font-bold text-amber-600">
                        {totalGaps}
                      </div>
                      <div className="text-xs text-gray-600 mt-1 font-medium">
                        {t.potentialGaps}
                      </div>
                    </div>
                  </div>
                </div>

                {displayRecs.length === 0 ? (
                  <div className="card p-8 text-center text-gray-500">
                    {t.noStandardsFound}
                  </div>
                ) : (
                  <div className="space-y-4">
                    {displayRecs.map((rec, idx) => (
                      <RecommendationCard key={rec.id} recommendation={rec} index={idx + 1} />
                    ))}
                  </div>
                )}

                {/* ── Footer Warnings ───────────────────────────── */}
                {(totalGaps > 0 || versionIssues > 0) && (
                  <div className="card p-4 space-y-2">
                    {totalGaps > 0 && (
                      <div className="flex items-center gap-2 text-sm text-amber-700">
                        <span className="text-amber-500">⚠</span>
                        <span className="font-medium">{totalGaps} {t.specGapsWarning}</span>
                      </div>
                    )}
                    {versionIssues > 0 && (
                      <div className="flex items-center gap-2 text-sm text-amber-700">
                        <span className="text-amber-500">⚠</span>
                        <span className="font-medium">{versionIssues} {t.versionIssuesWarning}</span>
                      </div>
                    )}
                  </div>
                )}
              </>
            )
          })()}
        </div>
      )}
    </div>
  )
}
