import React, { useState, useRef, useCallback } from 'react'
import { api, ReportResponse, TenderStatusResponse, TenderDetailResponse, RequirementItem } from '@/api/client'
import { useTranslation } from '@/i18n/LanguageContext'
import { RecommendationCard } from './RecommendationCard'
import { ProgressBar } from './ProgressBar'

interface TenderWorkflowProps {
  onBack: () => void
}

type TenderStep = 'upload' | 'processing' | 'results'

export const TenderWorkflow: React.FC<TenderWorkflowProps> = ({ onBack }) => {
  const { t } = useTranslation()
  const [step, setStep] = useState<TenderStep>('upload')
  const [file, setFile] = useState<File | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const [tenderId, setTenderId] = useState<string | null>(null)
  const [tenderDetails, setTenderDetails] = useState<TenderDetailResponse | null>(null)
  const [requirements, setRequirements] = useState<RequirementItem[]>([])
  const [tenderStatus, setTenderStatus] = useState<TenderStatusResponse | null>(null)
  const [report, setReport] = useState<ReportResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const cleanup = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }, [])

  const handleFileSelect = (selectedFile: File) => {
    if (!selectedFile.name.toLowerCase().endsWith('.pdf')) {
      setError('Only PDF files are accepted.')
      return
    }
    if (selectedFile.size > 50 * 1024 * 1024) {
      setError('File exceeds 50MB limit.')
      return
    }
    setError(null)
    setFile(selectedFile)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile) handleFileSelect(droppedFile)
  }

  const handleUploadAndAnalyze = async () => {
    if (!file) return
    cleanup()
    setIsUploading(true)
    setError(null)

    try {
      const uploadRes = await api.uploadTender(file)
      const currentTenderId = uploadRes.id
      setTenderId(currentTenderId)

      // Start the tender analysis pipeline on the backend
      await api.startTenderAnalysis(currentTenderId)

      setStep('processing')
      setIsUploading(false)

      let attempts = 0
      const maxAttempts = 150  // 5 minutes (150 * 2000ms)

      pollRef.current = setInterval(async () => {
        attempts++
        try {
          const statusRes = await api.getTenderStatus(currentTenderId)
          setTenderStatus(statusRes)

          if (statusRes.status === 'completed') {
            cleanup()
            const [details, reqs, rep] = await Promise.all([
              api.getTenderDetails(currentTenderId),
              api.getTenderRequirements(currentTenderId),
              api.getTenderReport(currentTenderId),
            ])
            setTenderDetails(details)
            setRequirements(reqs || [])
            setReport(rep)
            setStep('results')
          } else if (statusRes.status === 'failed') {
            cleanup()
            setError(statusRes.message || t.stageLabels.failed || 'Analysis failed.')
            setStep('upload')
          }

          if (attempts >= maxAttempts) {
            cleanup()
            setError('Processing timed out. The server may still be processing.')
            setStep('upload')
          }
        } catch (pollErr) {
          console.error('Polling error:', pollErr)
        }
      }, 2000)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
      setIsUploading(false)
    }
  }

  const handleReset = () => {
    cleanup()
    setStep('upload')
    setFile(null)
    setTenderId(null)
    setTenderDetails(null)
    setRequirements([])
    setTenderStatus(null)
    setReport(null)
    setError(null)
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Back + Title */}
      <div>
        <button onClick={onBack} className="text-sm text-navy-700 hover:underline mb-2">
          {t.backToHome}
        </button>
        <h1 className="text-2xl font-bold text-gray-900">{t.tenderTitle}</h1>
        <p className="text-sm text-gray-600 mt-1">
          {t.tenderSubtitle}
        </p>
      </div>

      {/* Error */}
      {error && (
        <div className="card p-4 border-red-200 bg-red-50">
          <div className="flex items-center gap-2 text-sm text-red-800">
            <span className="font-semibold">Error:</span>
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Step 1: Upload */}
      {step === 'upload' && (
        <div className="card p-6">
          <div
            className={`border-2 border-dashed rounded-lg p-10 text-center transition-colors cursor-pointer ${
              dragOver ? 'border-navy-500 bg-navy-50' : 'border-gray-300 hover:border-gray-400'
            }`}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0]
                if (f) handleFileSelect(f)
              }}
            />
            <svg className="w-10 h-10 mx-auto text-gray-400 mb-3" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" />
            </svg>
            {file ? (
              <div>
                <p className="text-sm font-semibold text-gray-900">{file.name}</p>
                <p className="text-xs text-gray-500 mt-1">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
              </div>
            ) : (
              <div>
                <p className="text-sm text-gray-700">
                  <span className="font-semibold text-navy-700">{t.uploadDropTitle}</span>
                </p>
                <p className="text-xs text-gray-500 mt-1">{t.uploadDropSub}</p>
              </div>
            )}
          </div>

          {file && (
            <div className="flex items-center gap-3 mt-4">
              <button
                onClick={handleUploadAndAnalyze}
                disabled={isUploading}
                className="btn-primary"
              >
                {isUploading ? (
                  <>
                    <svg className="w-4 h-4 animate-spin-slow" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    {t.analyzingTender}
                  </>
                ) : (
                  t.btnAnalyzeTender
                )}
              </button>
              <button
                onClick={() => { setFile(null); setError(null) }}
                className="btn-outline"
              >
                Clear
              </button>
            </div>
          )}
        </div>
      )}

      {/* Step 2: Processing */}
      {step === 'processing' && tenderStatus && (
        <div className="card p-6">
          <h2 className="section-title mb-4">{t.analyzingTender}</h2>
          <ProgressBar
            progress={tenderStatus.progress || 0}
            label={
              (tenderStatus.processing_status && t.stageLabels[tenderStatus.processing_status]) ||
              tenderStatus.processing_status ||
              t.processingTitle
            }
          />
          <p className="text-xs text-gray-500 mt-3">
            This may take a few moments while requirements are extracted and verified against BIS standards.
          </p>
        </div>
      )}

      {/* Step 3: Results */}
      {step === 'results' && (
        <>
          {/* ── Summary Header ────────────────────────────── */}
          {(() => {
            const displayRecs = (report?.recommendations || []).slice(0, 4)
            const totalGaps = displayRecs.reduce((sum, r) => sum + (r.gaps?.length || 0), 0)
            const versionIssues = displayRecs.filter(
              r => r.version_info && !r.version_info.is_current
            ).length

            return (
              <>
                <div className="card p-6">
                  <h2 className="text-xl font-bold text-navy-800 mb-4 tracking-tight">
                    {t.tenderReview}
                  </h2>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="p-4 bg-navy-50 rounded-lg text-center">
                      <div className="text-2xl font-bold text-navy-800">
                        {requirements.length}
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

                {/* ── Per-Requirement Cards ─────────────────────── */}
                {displayRecs.length > 0 && (
                  <div className="space-y-4">
                    {displayRecs.map((rec, idx) => (
                      <RecommendationCard key={rec.id} recommendation={rec} index={idx + 1} />
                    ))}
                  </div>
                )}

                {displayRecs.length === 0 && (
                  <div className="card p-8 text-center text-gray-500">
                    {t.noStandardsFound}
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

          {report?.compliance_note && (
            <div className="card p-4 border-amber-200 bg-amber-50">
              <div className="text-sm">
                <span className="font-semibold text-amber-800">Note: </span>
                <span className="text-amber-700">{report.compliance_note}</span>
              </div>
            </div>
          )}

          {/* New Analysis */}
          <div className="flex justify-center pt-4">
            <button onClick={handleReset} className="btn-outline">
              {t.btnAnalyzeAnother}
            </button>
          </div>
        </>
      )}
    </div>
  )
}
