/**
 * Procura API Client
 * Connects frontend directly to FastAPI backend endpoints.
 */

export interface HealthResponse {
  status: string
  service: string
  version?: string
}

export interface TenderUploadResponse {
  id: string
  filename: string
  status: string
  message: string
}

export interface TenderStatusResponse {
  id: string
  status: string
  processing_status?: string | null
  progress?: number | null
  message?: string | null
}

export interface TenderSection {
  id: string
  page_start?: number | null
  page_end?: number | null
  section_title?: string | null
  section_type: string
  content?: string | null
  priority: string // "high" | "medium" | "low"
}

export interface TenderDetailResponse {
  id: string
  title?: string | null
  filename: string
  status: string
  processing_status?: string | null
  page_count?: number | null
  language?: string | null
  sections: TenderSection[]
  created_at: string
}

export interface RequirementItem {
  id: string
  requirement: string
  normalized_requirement?: string | null
  requirement_type: string
  parameters?: Record<string, any> | null
  source: string
}

export interface CoverageItem {
  category: string
  status: string // "covered" | "partial" | "missing" | "not_applicable"
}

export interface RelatedStandard {
  standard_number: string
  title: string
  reference_type: string
  description?: string | null
}

export interface VersionInfo {
  edition?: string | null
  status?: string | null
  amendments?: any[] | null
  is_current?: boolean
  note?: string | null
}

export interface CertificationInfo {
  certification_required?: boolean | null
  certification_details?: string | null
  verified?: boolean
  note?: string | null
}

export interface RecommendationItem {
  id: string
  standard_number: string
  standard_title: string
  relevance_score?: number | null
  confidence_score?: number | null
  compliance_score?: number | null
  applicable: boolean
  applicability_level: string // "HIGH" | "MEDIUM" | "LOW"
  reasoning?: string | null
  coverage: CoverageItem[]
  gaps: string[]
  related_standards: RelatedStandard[]
  version_info?: VersionInfo | null
  certification_info?: CertificationInfo | null
  status: string // "pending" | "accepted" | "rejected" | "under_review"
}

export interface ReportResponse {
  source_type: string // "tender" | "query"
  source_id: string
  total_requirements: number
  total_standards_evaluated: number
  recommendations: RecommendationItem[]
  compliance_note?: string | null
  generated_at: string
}

export interface QueryResponse {
  id: string
  query_text: string
  status: string
  message: string
}

export interface QueryDetailResponse {
  id: string
  query_text: string
  normalized_query?: string | null
  status: string
  requirements: RequirementItem[]
  created_at: string
}

export interface RecommendationActionResponse {
  id: string
  status: string
  message: string
}

const API_BASE = (import.meta.env.VITE_API_URL || "https://procura-zhj7.onrender.com").replace(/\/$/, "")

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
  })

  if (!res.ok) {
    let errorDetail = res.statusText
    try {
      const errJson = await res.json()
      errorDetail = errJson.detail || errJson.message || JSON.stringify(errJson)
    } catch {
      if (res.status === 404) {
        errorDetail = `Endpoint not found (404) at ${url}`
      }
    }
    throw new Error(`API Error ${res.status}: ${errorDetail}`)
  }

  return res.json()
}

export const api = {
  // System Health
  async checkHealth(): Promise<HealthResponse> {
    return request<HealthResponse>("/health")
  },

  // Tender PDF Flow
  async uploadTender(file: File): Promise<TenderUploadResponse> {
    const formData = new FormData()
    formData.append("file", file)
    const res = await fetch(`${API_BASE}/api/tenders/upload`, {
      method: "POST",
      body: formData,
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || "Failed to upload tender PDF")
    }
    return res.json()
  },

  async startTenderAnalysis(tenderId: string): Promise<{ tender_id: string; job_id: string; status: string; message: string }> {
    return request(`/api/tenders/${tenderId}/analyze`, { method: "POST" })
  },

  async getTenderStatus(tenderId: string): Promise<TenderStatusResponse> {
    return request<TenderStatusResponse>(`/api/tenders/${tenderId}/status`)
  },

  async getTenderDetails(tenderId: string): Promise<TenderDetailResponse> {
    return request<TenderDetailResponse>(`/api/tenders/${tenderId}`)
  },

  async getTenderRequirements(tenderId: string): Promise<RequirementItem[]> {
    return request<RequirementItem[]>(`/api/tenders/${tenderId}/requirements`)
  },

  async getTenderReport(tenderId: string): Promise<ReportResponse> {
    return request<ReportResponse>(`/api/tenders/${tenderId}/report`)
  },

  // Query Flow
  async submitQuery(queryText: string): Promise<QueryResponse> {
    return request<QueryResponse>("/api/query", {
      method: "POST",
      body: JSON.stringify({ query: queryText }),
    })
  },

  async getQueryDetails(queryId: string): Promise<QueryDetailResponse> {
    return request<QueryDetailResponse>(`/api/query/${queryId}`)
  },

  async getQueryReport(queryId: string): Promise<ReportResponse> {
    return request<ReportResponse>(`/api/query/${queryId}/report`)
  },

  // Officer Action Flow
  async acceptRecommendation(recommendationId: string, reason?: string): Promise<RecommendationActionResponse> {
    return request<RecommendationActionResponse>(`/api/recommendations/${recommendationId}/accept`, {
      method: "POST",
      body: JSON.stringify({ reason: reason || null }),
    })
  },

  async rejectRecommendation(recommendationId: string, reason?: string): Promise<RecommendationActionResponse> {
    return request<RecommendationActionResponse>(`/api/recommendations/${recommendationId}/reject`, {
      method: "POST",
      body: JSON.stringify({ reason: reason || null }),
    })
  },

  async reviewRecommendation(recommendationId: string, reason?: string): Promise<RecommendationActionResponse> {
    return request<RecommendationActionResponse>(`/api/recommendations/${recommendationId}/review`, {
      method: "POST",
      body: JSON.stringify({ reason: reason || null }),
    })
  },

  // BIS Standards & Knowledge Base
  async getStandardsStats(): Promise<{
    total_standards: number
    embedded_standards: number
    total_references: number
    embedding_dimension: number
    embedding_model: string
    categories: Record<string, number>
  }> {
    return request(`/api/standards/stats`)
  },
}
