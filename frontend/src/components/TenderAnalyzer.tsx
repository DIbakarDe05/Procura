import React, { useState, useRef } from 'react'
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Layers,
  ChevronRight,
  Shield,
  FileCheck,
  AlertTriangle
} from 'lucide-react'
import { api, TenderUploadResponse, TenderDetailResponse, ReportResponse, RequirementItem } from '@/api/client'
import { RecommendationCard } from './RecommendationCard'

export const TenderAnalyzer: React.FC = () => {
  const [file, setFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadedTender, setUploadedTender] = useState<TenderUploadResponse | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [stageMessage, setStageMessage] = useState('')
  const [tenderDetails, setTenderDetails] = useState<TenderDetailResponse | null>(null)
  const [requirements, setRequirements] = useState<RequirementItem[]>([])
  const [report, setReport] = useState<ReportResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0]
      if (!selected.name.toLowerCase().endsWith('.pdf')) {
        setError('Please upload a valid PDF tender document.')
        return
      }
      setFile(selected)
      setError(null)
      setUploadedTender(null)
      setTenderDetails(null)
      setReport(null)
      setProgress(0)
    }
  }

  const handleUpload = async () => {
    if (!file) return
    setIsUploading(true)
    setError(null)
    try {
      const res = await api.uploadTender(file)
      setUploadedTender(res)
      setIsUploading(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
      setIsUploading(false)
    }
  }

  const handleStartAnalysis = async () => {
    if (!uploadedTender) return
    setIsAnalyzing(true)
    setError(null)
    setProgress(5)
    setStageMessage('Initializing document extraction engine (PyMuPDF & Tesseract OCR)...')

    try {
      await api.startTenderAnalysis(uploadedTender.id)

      let attempts = 0
      const maxAttempts = 60

      const poll = setInterval(async () => {
        attempts++
        try {
          const statusRes = await api.getTenderStatus(uploadedTender.id)
          const prog = statusRes.progress || 10
          setProgress(prog)

          if (statusRes.processing_status === 'processing_pdf') {
            setStageMessage('Extracting pages & applying OCR to scanned sections...')
          } else if (statusRes.processing_status === 'extracting_requirements') {
            setStageMessage('Categorizing sections & extracting technical specifications...')
          } else if (statusRes.processing_status === 'generating_embeddings') {
            setStageMessage('Generating 3072-dim embeddings for requirements...')
          } else if (statusRes.processing_status === 'retrieving_standards') {
            setStageMessage('Executing vector similarity search against BIS catalog...')
          } else if (statusRes.processing_status === 'analyzing_top_k') {
            setStageMessage('Evaluating standard coverage with Gemini 3.1 Flash-Lite...')
          } else if (statusRes.processing_status === 'calculating_scores') {
            setStageMessage('Calculating Relevance, Compliance, and Confidence scores...')
          } else if (statusRes.processing_status === 'building_report') {
            setStageMessage('Building structured audit report with certification info...')
          }

          if (statusRes.status === 'completed') {
            clearInterval(poll)
            setProgress(100)
            setStageMessage('Tender analysis complete!')

            // Fetch details, requirements, and full report
            const [details, reqs, rep] = await Promise.all([
              api.getTenderDetails(uploadedTender.id),
              api.getTenderRequirements(uploadedTender.id),
              api.getTenderReport(uploadedTender.id),
            ])

            setTenderDetails(details)
            setRequirements(reqs)
            setReport(rep)
            setIsAnalyzing(false)
          } else if (statusRes.status === 'failed') {
            clearInterval(poll)
            setError(statusRes.message || 'Tender analysis failed.')
            setIsAnalyzing(false)
          }

          if (attempts >= maxAttempts) {
            clearInterval(poll)
            setError('Analysis timed out. Please refresh or retry.')
            setIsAnalyzing(false)
          }
        } catch (pollErr) {
          console.error('Polling status error:', pollErr)
        }
      }, 1500)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
      setIsAnalyzing(false)
    }
  }

  const getPriorityBadge = (priority: string) => {
    switch (priority.toLowerCase()) {
      case 'high':
        return 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
      case 'medium':
        return 'bg-indigo-500/15 text-indigo-300 border-indigo-500/30'
      default:
        return 'bg-slate-800 text-slate-400 border-slate-700'
    }
  }

  return (
    <div className="space-y-8 pb-16">
      {/* Header Banner */}
      <div className="glass-panel rounded-3xl border border-slate-800 p-6 sm:p-8">
        <div className="flex items-center gap-2 text-indigo-400 font-semibold text-xs uppercase tracking-wider mb-2">
          <Shield className="h-4 w-4" />
          <span>Procurement Document Processing</span>
        </div>
        <h1 className="font-display text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          Tender PDF Standards Compliance Analyzer
        </h1>
        <p className="mt-2 text-sm text-slate-300 leading-relaxed max-w-3xl">
          Upload procurement tender PDFs. Procura automatically applies Tesseract OCR for scanned pages, separates technical requirements from administrative clauses, retrieves candidate Indian Standards from our database, and evaluates them with Gemini.
        </p>

        {/* Upload Zone */}
        <div className="mt-6 rounded-2xl border-2 border-dashed border-slate-700/80 bg-slate-900/40 p-8 text-center transition-colors hover:border-indigo-500/50">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".pdf"
            className="hidden"
          />

          {!file ? (
            <div className="flex flex-col items-center">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-500/10 text-indigo-400 ring-1 ring-indigo-500/20 mb-3">
                <UploadCloud className="h-7 w-7" />
              </div>
              <p className="text-sm font-semibold text-white">
                Drag and drop your tender PDF here, or{' '}
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="text-indigo-400 hover:text-indigo-300 underline underline-offset-2"
                >
                  browse files
                </button>
              </p>
              <p className="text-xs text-slate-500 mt-1">Supports digital, scanned, or mixed PDFs up to 50MB</p>
            </div>
          ) : (
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4 rounded-xl border border-slate-800 bg-slate-900 p-4">
              <div className="flex items-center gap-3 text-left">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500/20 text-indigo-400 shrink-0">
                  <FileText className="h-5 w-5" />
                </div>
                <div>
                  <div className="text-sm font-semibold text-white">{file.name}</div>
                  <div className="text-xs text-slate-400 font-mono">
                    {(file.size / (1024 * 1024)).toFixed(2)} MB • Ready for processing
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                {!uploadedTender ? (
                  <button
                    onClick={handleUpload}
                    disabled={isUploading}
                    className="flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-bold text-white hover:bg-indigo-500 disabled:opacity-50"
                  >
                    {isUploading ? (
                      <>
                        <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                        <span>Uploading...</span>
                      </>
                    ) : (
                      <>
                        <UploadCloud className="h-3.5 w-3.5" />
                        <span>Upload Document</span>
                      </>
                    )}
                  </button>
                ) : (
                  <button
                    onClick={handleStartAnalysis}
                    disabled={isAnalyzing}
                    className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-700 px-4 py-2 text-xs font-bold text-white shadow-lg shadow-indigo-600/30 hover:from-indigo-500 hover:to-indigo-600 disabled:opacity-50"
                  >
                    {isAnalyzing ? (
                      <>
                        <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                        <span>Analyzing...</span>
                      </>
                    ) : (
                      <>
                        <FileCheck className="h-3.5 w-3.5" />
                        <span>Start Technical Analysis</span>
                      </>
                    )}
                  </button>
                )}

                <button
                  onClick={() => {
                    setFile(null)
                    setUploadedTender(null)
                  }}
                  disabled={isAnalyzing}
                  className="rounded-xl border border-slate-700 px-3 py-2 text-xs font-semibold text-slate-400 hover:bg-slate-800"
                >
                  Clear
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Live Stepper & Progress Bar */}
      {isAnalyzing && (
        <div className="glass-panel rounded-2xl border border-indigo-500/30 bg-indigo-950/20 p-5 animate-in fade-in">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2.5 text-sm font-semibold text-white">
              <RefreshCw className="h-4 w-4 animate-spin text-indigo-400" />
              <span>{stageMessage}</span>
            </div>
            <span className="text-xs font-mono font-bold text-indigo-300">{progress}%</span>
          </div>
          <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-indigo-500 via-cyan-400 to-emerald-400 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Error Banner */}
      {error && (
        <div className="flex items-center gap-3 rounded-2xl border border-rose-500/30 bg-rose-950/20 p-4 text-rose-300 text-sm">
          <AlertCircle className="h-5 w-5 shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Results View: Split-Pane Display */}
      {tenderDetails && report && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Document Anatomy & Extracted Requirements */}
          <div className="lg:col-span-5 space-y-4">
            {/* Document Overview Card */}
            <div className="glass-panel rounded-2xl border border-slate-800 p-5">
              <h3 className="font-display text-sm font-bold text-white mb-3 flex items-center gap-2">
                <FileText className="h-4 w-4 text-indigo-400" />
                <span>Document Anatomy</span>
              </h3>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-2.5">
                  <span className="text-slate-500 block">Total Pages</span>
                  <span className="font-bold text-white text-base">{tenderDetails.page_count || 1}</span>
                </div>
                <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-2.5">
                  <span className="text-slate-500 block">Identified Sections</span>
                  <span className="font-bold text-indigo-400 text-base">{tenderDetails.sections.length}</span>
                </div>
              </div>

              {/* Sections Breakdown */}
              <div className="mt-4">
                <span className="text-xs font-semibold text-slate-400 block mb-2">Detected Sections:</span>
                <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                  {tenderDetails.sections.map((sec, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between rounded-lg border border-slate-800/80 bg-slate-900/40 px-2.5 py-1.5 text-xs"
                    >
                      <span className="font-medium text-slate-300 truncate max-w-[180px]">
                        {sec.section_title || sec.section_type.replace('_', ' ')}
                      </span>
                      <span
                        className={`rounded px-1.5 py-0.5 text-[10px] font-semibold border uppercase ${getPriorityBadge(
                          sec.priority
                        )}`}
                      >
                        {sec.priority}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Extracted Requirements List */}
            <div className="glass-panel rounded-2xl border border-slate-800 p-5">
              <h3 className="font-display text-sm font-bold text-white mb-3 flex items-center gap-2">
                <Layers className="h-4 w-4 text-emerald-400" />
                <span>Extracted Requirements ({requirements.length})</span>
              </h3>
              <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
                {requirements.map((req, i) => (
                  <div
                    key={i}
                    className="rounded-xl border border-slate-800 bg-slate-900/60 p-2.5 text-xs space-y-1"
                  >
                    <div className="flex items-center justify-between">
                      <span className="rounded bg-indigo-500/15 px-1.5 py-0.5 text-[10px] font-semibold text-indigo-300 uppercase">
                        {req.requirement_type}
                      </span>
                    </div>
                    <p className="text-slate-200 font-medium">{req.requirement}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right Column: Applicable Standards Feed */}
          <div className="lg:col-span-7 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileCheck className="h-5 w-5 text-emerald-400" />
                <h2 className="font-display text-lg font-bold text-white">
                  Applicable Indian Standards ({report.recommendations.length})
                </h2>
              </div>
              <span className="text-xs font-mono text-slate-400">
                Generated: {new Date(report.generated_at).toLocaleTimeString()}
              </span>
            </div>

            {report.recommendations.length === 0 ? (
              <div className="glass-panel rounded-2xl p-8 text-center text-slate-400">
                No matching standards found in the verified database for this document.
              </div>
            ) : (
              <div className="space-y-4">
                {report.recommendations.map((rec) => (
                  <RecommendationCard key={rec.id} recommendation={rec} />
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
