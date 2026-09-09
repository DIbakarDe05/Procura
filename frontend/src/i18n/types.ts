export type Language = 'en' | 'hi' | 'bn' | 'mr' | 'ta' | 'gu'

export interface LanguageOption {
  code: Language
  label: string
  nativeName: string
}

export const SUPPORTED_LANGUAGES: LanguageOption[] = [
  { code: 'en', label: 'English', nativeName: 'English' },
  { code: 'hi', label: 'Hindi', nativeName: 'हिन्दी' },
  { code: 'bn', label: 'Bengali', nativeName: 'বাংলা' },
  { code: 'mr', label: 'Marathi', nativeName: 'मराठी' },
  { code: 'ta', label: 'Tamil', nativeName: 'தமிழ்' },
  { code: 'gu', label: 'Gujarati', nativeName: 'ગુજરાતી' },
]

export interface Translations {
  // Navigation & Header
  portalTitle: string
  portalSubtitle: string
  navHome: string
  navQuery: string
  navTender: string
  statusOnline: string
  statusOffline: string
  statusConnecting: string
  langSelect: string

  // Landing Page
  heroBadge: string
  heroTitle: string
  heroSubtitle: string
  cardTenderTitle: string
  cardTenderDesc: string
  cardQueryTitle: string
  cardQueryDesc: string
  featuresTitle: string
  featZeroHallucination: string
  featZeroHallucinationDesc: string
  featGapAnalysis: string
  featGapAnalysisDesc: string
  featVersionCheck: string
  featVersionCheckDesc: string
  featOfficerAudit: string
  featOfficerAuditDesc: string
  statStandards: string
  statAccuracy: string
  statTurnaround: string
  statAlignment: string

  // Query Workflow
  backToHome: string
  queryTitle: string
  querySubtitle: string
  queryPlaceholder: string
  charCount: string
  btnRecommend: string
  btnAnalyzing: string
  extractedReqs: string
  processingTitle: string
  standardsReview: string
  reqsAnalyzed: string
  topStdsRecommended: string
  potentialGaps: string
  noStandardsFound: string
  specGapsWarning: string
  versionIssuesWarning: string
  genericQueryNote: string

  // Tender Workflow
  tenderTitle: string
  tenderSubtitle: string
  uploadDropTitle: string
  uploadDropSub: string
  btnSelectFile: string
  btnAnalyzeTender: string
  analyzingTender: string
  tenderReview: string
  btnAnalyzeAnother: string
  stageLabels: Record<string, string>

  // Recommendation Card
  recommendationNum: string
  recommendedLabel: string
  relevance: string
  confidence: string
  compliance: string
  whyLabel: string
  relatedStandards: string
  btnAccept: string
  btnReject: string
  btnViewDetails: string
  btnHideDetails: string
  coverageTitle: string
  colCategory: string
  colStatus: string
  gapsTitle: string
  versionInfoTitle: string
  edition: string
  status: string
  current: string
  yes: string
  no: string
  amendments: string
  none: string
  certificationTitle: string
  required: string
  notRequired: string
  details: string
  statusAccepted: string
  statusRejected: string
  statusPending: string

  // Coverage status
  covCovered: string
  covPartial: string
  covMissing: string
  covNA: string

  // Footer
  footerTitle: string
  footerMinistry: string
  footerDisclaimer: string
}
