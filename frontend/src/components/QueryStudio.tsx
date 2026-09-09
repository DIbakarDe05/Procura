import React, { useState } from 'react'
import { Sparkles, Send, AlertCircle, RefreshCw, Layers, CheckCircle, FileCheck, ArrowRight } from 'lucide-react'
import { api, ReportResponse, QueryDetailResponse } from '@/api/client'
import { RecommendationCard } from './RecommendationCard'
import { GradientBackground } from '@/components/ui/jade-sky'

export const QueryStudio: React.FC = () => {
  const [queryText, setQueryText] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [statusMessage, setStatusMessage] = useState('')
  const [queryDetails, setQueryDetails] = useState<QueryDetailResponse | null>(null)
  const [report, setReport] = useState<ReportResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (textToSubmit?: string) => {
    const text = textToSubmit || queryText
    if (!text.trim()) return


    setIsSubmitting(true)
    setError(null)
    setReport(null)
    setQueryDetails(null)
    setStatusMessage('Submitting technical specification query to Procura engine...')

    try {
      // 1. Submit query
      const submitRes = await api.submitQuery(text)
      const queryId = submitRes.id

      // 2. Poll for completion
      setStatusMessage('Parsing requirements & retrieving candidate BIS standards...')

      let attempts = 0
      const maxAttempts = 30

      const pollInterval = setInterval(async () => {
        attempts++
        try {
          const details = await api.getQueryDetails(queryId)
          setQueryDetails(details)

          if (details.status === 'processing') {
            setStatusMessage('Generating 3072-dim embeddings & computing cosine similarities...')
          } else if (details.status === 'analyzing') {
            setStatusMessage('Evaluating standard coverage with Gemini 3.1 Flash-Lite...')
          } else if (details.status === 'completed') {
            clearInterval(pollInterval)
            setStatusMessage('Compiling final structured recommendation report...')

            // Fetch report
            const rep = await api.getQueryReport(queryId)
            setReport(rep)
            setIsSubmitting(false)
            setStatusMessage('')
          } else if (details.status === 'failed') {
            clearInterval(pollInterval)
            setError('Query analysis failed on server. Please try again.')
            setIsSubmitting(false)
          }

          if (attempts >= maxAttempts) {
            clearInterval(pollInterval)
            setError('Analysis timed out. The server may still be processing in the background.')
            setIsSubmitting(false)
          }
        } catch (pollErr) {
          console.error('Polling error:', pollErr)
        }
      }, 1500)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
      setIsSubmitting(false)
    }
  }

  return (
    <div className="space-y-8 pb-16">
      {/* Hero Header with Integrated Jade Sky Gradient Background */}
      <div className="relative overflow-hidden rounded-3xl border border-slate-800 shadow-2xl">
        {/* Jade Sky Gradient Component */}
        <div className="absolute inset-0 opacity-25">
          <GradientBackground className="h-full w-full" />
        </div>

        {/* Hero Content Overlay */}
        <div className="relative z-10 p-6 sm:p-10 backdrop-blur-xl bg-slate-950/70">
          <div className="inline-flex items-center gap-2 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-3 py-1 text-xs font-semibold text-indigo-300 mb-4">
            <Sparkles className="h-3.5 w-3.5 text-indigo-400" />
            <span>Natural-Language Standards Retrieval</span>
          </div>

          <h1 className="font-display text-2xl sm:text-4xl font-extrabold text-white tracking-tight leading-tight">
            Procurement Technical Query Studio
          </h1>
          <p className="mt-2.5 max-w-3xl text-sm sm:text-base text-slate-300 leading-relaxed">
            Enter equipment specifications, operating parameters, or material grades. Procura decomposes the requirement into technical dimensions, matches them against 20 verified BIS standards using 3072-dimensional vector search, and calculates independent Relevance, Confidence, and Compliance scores.
          </p>
        </div>
      </div>

      {/* Query Input Box */}
      <div className="glass-panel rounded-2xl border border-slate-800 p-5 shadow-xl">
        <label className="block font-display text-sm font-bold text-white mb-2">
          Technical Specification or Equipment Description:
        </label>
        <div className="relative">
          <textarea
            rows={3}
            value={queryText}
            onChange={(e) => setQueryText(e.target.value)}
            placeholder="e.g. 10 HP horizontal centrifugal water pump operating at 2900 RPM with stainless steel casing for cold water supply..."
            className="w-full rounded-xl border border-slate-800 bg-slate-900/90 p-4 text-sm text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 transition-all font-sans leading-relaxed"
          />
          <button
            onClick={() => handleSubmit()}
            disabled={isSubmitting || !queryText.trim()}
            className="absolute bottom-3 right-3 flex items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-700 px-4 py-2 text-xs font-bold text-white shadow-lg shadow-indigo-600/30 hover:from-indigo-500 hover:to-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {isSubmitting ? (
              <>
                <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                <span>Analyzing...</span>
              </>
            ) : (
              <>
                <Send className="h-3.5 w-3.5" />
                <span>Recommend Standards</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Live Processing Stepper Indicator */}
      {isSubmitting && (
        <div className="glass-panel rounded-2xl border border-indigo-500/30 bg-indigo-950/20 p-5 animate-in fade-in">
          <div className="flex items-center gap-3">
            <RefreshCw className="h-5 w-5 animate-spin text-indigo-400" />
            <div>
              <div className="text-sm font-semibold text-white">Pipeline Executing</div>
              <div className="text-xs text-indigo-300 font-mono mt-0.5">{statusMessage}</div>
            </div>
          </div>
          <div className="mt-3 h-1.5 w-full rounded-full bg-slate-800 overflow-hidden">
            <div className="h-full bg-gradient-to-r from-indigo-500 via-cyan-400 to-emerald-400 rounded-full animate-pulse w-3/4" />
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="flex items-center gap-3 rounded-2xl border border-rose-500/30 bg-rose-950/20 p-4 text-rose-300 text-sm">
          <AlertCircle className="h-5 w-5 shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Query Decomposition Breakdown Card */}
      {queryDetails && (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <div className="flex items-center gap-2 font-display text-sm font-bold text-white mb-3">
            <Layers className="h-4 w-4 text-indigo-400" />
            <span>Specification Decomposition & Parameter Extraction</span>
          </div>

          <div className="space-y-2">
            <div className="flex items-start gap-2 text-xs">
              <span className="text-slate-400 font-semibold w-24 shrink-0">Raw Query:</span>
              <span className="text-slate-200 font-mono">{queryDetails.query_text}</span>
            </div>

            {queryDetails.requirements && queryDetails.requirements.length > 0 && (
              <div className="mt-3">
                <span className="text-xs text-slate-400 font-semibold block mb-1.5">
                  Extracted Technical Attributes ({queryDetails.requirements.length}):
                </span>
                <div className="flex flex-wrap gap-2">
                  {queryDetails.requirements.map((r, i) => (
                    <div
                      key={i}
                      className="rounded-lg border border-slate-800 bg-slate-950 px-2.5 py-1 text-xs text-slate-300"
                    >
                      <span className="text-indigo-400 font-semibold uppercase text-[10px] mr-1.5">
                        [{r.requirement_type}]
                      </span>
                      <span>{r.requirement}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Generic Query Notice Banner (When Compliance is Null) */}
      {report?.compliance_note && (
        <div className="flex items-start gap-3 rounded-2xl border border-amber-500/30 bg-amber-950/25 p-4 text-xs text-amber-200">
          <AlertCircle className="h-5 w-5 shrink-0 text-amber-400 mt-0.5" />
          <div>
            <span className="font-bold text-amber-300 text-sm block">Generic Query Detected</span>
            <p className="mt-1 text-amber-200/90 leading-relaxed">
              {report.compliance_note}
            </p>
          </div>
        </div>
      )}

      {/* Recommendation Results Feed */}
      {report && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileCheck className="h-5 w-5 text-emerald-400" />
              <h2 className="font-display text-lg font-bold text-white">
                Applicable BIS Standards ({report.recommendations.length} Identified)
              </h2>
            </div>
            <span className="text-xs font-mono text-slate-400">
              Generated: {new Date(report.generated_at).toLocaleTimeString()}
            </span>
          </div>

          {report.recommendations.length === 0 ? (
            <div className="glass-panel rounded-2xl p-8 text-center text-slate-400">
              No matching standards found in the verified database for this query.
            </div>
          ) : (
            <div className="space-y-4">
              {report.recommendations.map((rec) => (
                <RecommendationCard key={rec.id} recommendation={rec} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
