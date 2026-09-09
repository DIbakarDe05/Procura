import React, { useState } from 'react'
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  ChevronDown,
  ChevronUp,
  ShieldCheck,
  Award,
  Network,
  Check,
  X,
  Clock,
  AlertCircle
} from 'lucide-react'
import { RecommendationItem, api } from '@/api/client'

interface RecommendationCardProps {
  recommendation: RecommendationItem
  onStatusUpdate?: (id: string, newStatus: string) => void
}

export const RecommendationCard: React.FC<RecommendationCardProps> = ({
  recommendation,
  onStatusUpdate,
}) => {
  const [isExpanded, setIsExpanded] = useState(false)
  const [currentStatus, setCurrentStatus] = useState(recommendation.status)
  const [isActionLoading, setIsActionLoading] = useState(false)
  const [rejectReasonPrompt, setRejectReasonPrompt] = useState(false)
  const [rejectReason, setRejectReason] = useState('')

  const handleAction = async (action: 'accept' | 'reject' | 'review', reason?: string) => {
    setIsActionLoading(true)
    try {
      if (action === 'accept') {
        await api.acceptRecommendation(recommendation.id)
        setCurrentStatus('accepted')
        onStatusUpdate?.(recommendation.id, 'accepted')
      } else if (action === 'reject') {
        await api.rejectRecommendation(recommendation.id, reason)
        setCurrentStatus('rejected')
        onStatusUpdate?.(recommendation.id, 'rejected')
        setRejectReasonPrompt(false)
      } else if (action === 'review') {
        await api.reviewRecommendation(recommendation.id, reason)
        setCurrentStatus('under_review')
        onStatusUpdate?.(recommendation.id, 'under_review')
      }
    } catch (err) {
      alert(`Action failed: ${err instanceof Error ? err.message : String(err)}`)
    } finally {
      setIsActionLoading(false)
    }
  }

  // Helper for 9 coverage status icons & colors
  const getCoverageBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case 'covered':
        return {
          icon: <CheckCircle2 className="h-3 w-3 text-emerald-400" />,
          classes: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30',
        }
      case 'partial':
        return {
          icon: <AlertTriangle className="h-3 w-3 text-amber-400" />,
          classes: 'bg-amber-500/10 text-amber-300 border-amber-500/30',
        }
      case 'missing':
        return {
          icon: <XCircle className="h-3 w-3 text-rose-400" />,
          classes: 'bg-rose-500/10 text-rose-300 border-rose-500/30',
        }
      default:
        return {
          icon: <span className="h-1 w-2 bg-slate-500 rounded-full" />,
          classes: 'bg-slate-800/40 text-slate-400 border-slate-700/50',
        }
    }
  }

  const formatCategoryName = (name: string) => {
    return name
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (c) => c.toUpperCase())
  }

  return (
    <div className="glass-card rounded-2xl p-5 border border-slate-800 transition-all hover:border-slate-700 relative overflow-hidden">
      {/* Top Banner: Standard Title, Number & Status Badge */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
        <div>
          <div className="flex items-center flex-wrap gap-2">
            <span className="font-display text-lg font-bold tracking-tight text-white">
              {recommendation.standard_number}
            </span>
            {recommendation.version_info?.edition && (
              <span className="rounded-md bg-slate-800 px-2 py-0.5 text-xs text-slate-300 font-medium border border-slate-700">
                Ed. {recommendation.version_info.edition}
              </span>
            )}
            <span
              className={`rounded-md px-2 py-0.5 text-xs font-semibold uppercase tracking-wider ${
                recommendation.applicability_level === 'HIGH'
                  ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                  : recommendation.applicability_level === 'MEDIUM'
                  ? 'bg-indigo-500/15 text-indigo-300 border border-indigo-500/30'
                  : 'bg-slate-800 text-slate-400'
              }`}
            >
              {recommendation.applicability_level} RELEVANCE
            </span>

            {/* Officer Review Status Badge */}
            {currentStatus !== 'pending' && (
              <span
                className={`rounded-md px-2 py-0.5 text-xs font-semibold flex items-center gap-1 ${
                  currentStatus === 'accepted'
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                    : currentStatus === 'rejected'
                    ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                    : 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                }`}
              >
                {currentStatus === 'accepted' && <Check className="h-3 w-3" />}
                {currentStatus === 'rejected' && <X className="h-3 w-3" />}
                {currentStatus === 'under_review' && <Clock className="h-3 w-3" />}
                {currentStatus.replace('_', ' ').toUpperCase()}
              </span>
            )}
          </div>

          <h4 className="mt-1 text-sm font-semibold text-slate-200 leading-snug">
            {recommendation.standard_title}
          </h4>
        </div>

        {/* Action Controls for Procurement Officer */}
        <div className="flex items-center gap-1.5 self-end sm:self-auto shrink-0">
          <button
            onClick={() => handleAction('accept')}
            disabled={isActionLoading || currentStatus === 'accepted'}
            title="Accept standard recommendation"
            className={`flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-medium transition-all ${
              currentStatus === 'accepted'
                ? 'bg-emerald-600/30 text-emerald-300 border border-emerald-500/50'
                : 'bg-emerald-600/10 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-600 hover:text-white'
            }`}
          >
            <Check className="h-3.5 w-3.5" />
            <span>Accept</span>
          </button>

          <button
            onClick={() => setRejectReasonPrompt(!rejectReasonPrompt)}
            disabled={isActionLoading || currentStatus === 'rejected'}
            title="Reject standard recommendation"
            className={`flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-medium transition-all ${
              currentStatus === 'rejected'
                ? 'bg-rose-600/30 text-rose-300 border border-rose-500/50'
                : 'bg-rose-600/10 text-rose-400 border border-rose-500/30 hover:bg-rose-600 hover:text-white'
            }`}
          >
            <X className="h-3.5 w-3.5" />
            <span>Reject</span>
          </button>

          <button
            onClick={() => handleAction('review')}
            disabled={isActionLoading || currentStatus === 'under_review'}
            title="Flag standard for technical committee review"
            className={`flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-medium transition-all ${
              currentStatus === 'under_review'
                ? 'bg-amber-600/30 text-amber-300 border border-amber-500/50'
                : 'bg-amber-600/10 text-amber-400 border border-amber-500/30 hover:bg-amber-600 hover:text-white'
            }`}
          >
            <Clock className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Review</span>
          </button>
        </div>
      </div>

      {/* Reject Reason Input Modal / Expansion */}
      {rejectReasonPrompt && (
        <div className="mt-3 rounded-xl border border-rose-500/30 bg-rose-950/30 p-3 text-xs">
          <label className="block text-rose-200 font-medium mb-1">
            Reason for Rejection (Optional):
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="e.g., Equipment uses alternate hydraulic specification"
              className="flex-1 rounded-lg border border-slate-700 bg-slate-900 px-2.5 py-1 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-rose-500"
            />
            <button
              onClick={() => handleAction('reject', rejectReason)}
              className="rounded-lg bg-rose-600 px-3 py-1 font-semibold text-white hover:bg-rose-500"
            >
              Confirm
            </button>
            <button
              onClick={() => setRejectReasonPrompt(false)}
              className="rounded-lg border border-slate-700 px-2 py-1 text-slate-400 hover:bg-slate-800"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Mandatory Certification Alert if present */}
      {recommendation.certification_info?.certification_required && (
        <div className="mt-3 flex items-center gap-2 rounded-xl border border-amber-500/30 bg-amber-500/10 px-3 py-1.5 text-xs text-amber-300">
          <Award className="h-4 w-4 shrink-0 text-amber-400" />
          <span>
            <strong className="font-semibold text-amber-200">Mandatory Certification:</strong>{' '}
            {recommendation.certification_info.certification_details ||
              'Compulsory BIS Certification Order Applicable'}
          </span>
        </div>
      )}

      {/* The 3-Score Cluster Display */}
      <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-3">
        {/* Relevance Score Card */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium">Relevance Score</span>
            <span className="text-xs font-bold text-indigo-400">
              {recommendation.relevance_score !== null && recommendation.relevance_score !== undefined
                ? `${recommendation.relevance_score}%`
                : 'N/A'}
            </span>
          </div>
          <div className="mt-2 h-2 w-full rounded-full bg-slate-800 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-indigo-500 to-cyan-400 rounded-full transition-all duration-500"
              style={{ width: `${recommendation.relevance_score || 0}%` }}
            />
          </div>
          <span className="mt-1 block text-[10px] text-slate-500">
            Semantic & Product Compatibility
          </span>
        </div>

        {/* Confidence Score Card */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium">Confidence Score</span>
            <span className="text-xs font-bold text-emerald-400">
              {recommendation.confidence_score !== null && recommendation.confidence_score !== undefined
                ? `${recommendation.confidence_score}%`
                : 'N/A'}
            </span>
          </div>
          <div className="mt-2 h-2 w-full rounded-full bg-slate-800 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-full transition-all duration-500"
              style={{ width: `${recommendation.confidence_score || 0}%` }}
            />
          </div>
          <span className="mt-1 block text-[10px] text-slate-500">
            Retrieval Margin & Evidence Weight
          </span>
        </div>

        {/* Compliance Score Card (Handles Generic Queries with Null) */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium">Compliance Score</span>
            <span
              className={`text-xs font-bold ${
                recommendation.compliance_score !== null && recommendation.compliance_score !== undefined
                  ? 'text-cyan-400'
                  : 'text-amber-400'
              }`}
            >
              {recommendation.compliance_score !== null && recommendation.compliance_score !== undefined
                ? `${recommendation.compliance_score}%`
                : 'Needs Specs'}
            </span>
          </div>
          <div className="mt-2 h-2 w-full rounded-full bg-slate-800 overflow-hidden">
            {recommendation.compliance_score !== null && recommendation.compliance_score !== undefined ? (
              <div
                className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full transition-all duration-500"
                style={{ width: `${recommendation.compliance_score}%` }}
              />
            ) : (
              <div className="h-full bg-amber-500/40 rounded-full w-full" />
            )}
          </div>
          <span className="mt-1 block text-[10px] text-slate-500">
            {recommendation.compliance_score !== null && recommendation.compliance_score !== undefined
              ? 'Coverage of Requirements'
              : 'Generic Query (Requires Specs)'}
          </span>
        </div>
      </div>

      {/* 9-Category Coverage Matrix */}
      {recommendation.coverage && recommendation.coverage.length > 0 && (
        <div className="mt-4">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Coverage Analysis Checklist (9 Dimensions)
          </div>
          <div className="flex flex-wrap gap-1.5">
            {recommendation.coverage.map((item, idx) => {
              const badge = getCoverageBadge(item.status)
              return (
                <div
                  key={idx}
                  className={`flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-xs font-medium ${badge.classes}`}
                >
                  {badge.icon}
                  <span>{formatCategoryName(item.category)}</span>
                  <span className="text-[10px] opacity-75 font-mono">({item.status})</span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Expand / Collapse Details Button */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="mt-4 flex w-full items-center justify-between border-t border-slate-800/80 pt-3 text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors"
      >
        <span>
          {isExpanded ? 'Hide Technical Reasoning & Network' : 'View AI Reasoning, Missing Gaps & Normative Graph'}
        </span>
        {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
      </button>

      {/* Expandable Technical Reasoning, Gaps & Linked Standards */}
      {isExpanded && (
        <div className="mt-3 space-y-3 pt-1 text-xs border-t border-slate-800/40 animate-in fade-in duration-200">
          {/* AI Reasoning */}
          {recommendation.reasoning && (
            <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-3">
              <div className="font-semibold text-slate-300 flex items-center gap-1.5 mb-1">
                <ShieldCheck className="h-3.5 w-3.5 text-indigo-400" />
                <span>Technical Justification (Gemini 3.1 Flash-Lite):</span>
              </div>
              <p className="text-slate-400 leading-relaxed">{recommendation.reasoning}</p>
            </div>
          )}

          {/* Missing Gaps */}
          {recommendation.gaps && recommendation.gaps.length > 0 && (
            <div className="rounded-xl border border-rose-500/20 bg-rose-950/20 p-3">
              <div className="font-semibold text-rose-300 flex items-center gap-1.5 mb-1.5">
                <AlertCircle className="h-3.5 w-3.5 text-rose-400" />
                <span>Specific Coverage Gaps:</span>
              </div>
              <ul className="list-disc list-inside space-y-1 text-slate-300">
                {recommendation.gaps.map((gap, i) => (
                  <li key={i}>{gap}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Normative References Network */}
          {recommendation.related_standards && recommendation.related_standards.length > 0 && (
            <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-3">
              <div className="font-semibold text-slate-300 flex items-center gap-1.5 mb-2">
                <Network className="h-3.5 w-3.5 text-cyan-400" />
                <span>Linked Normative References & Test Standards:</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {recommendation.related_standards.map((rel, i) => (
                  <div
                    key={i}
                    className="flex flex-col rounded-lg border border-slate-800 bg-slate-950/60 p-2 text-[11px]"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-white">{rel.standard_number}</span>
                      <span className="rounded bg-indigo-500/20 px-1.5 py-0.5 text-[9px] font-mono text-indigo-300 uppercase">
                        {rel.reference_type.replace('_', ' ')}
                      </span>
                    </div>
                    <span className="text-slate-400 text-[10px] mt-0.5 truncate">{rel.title}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
