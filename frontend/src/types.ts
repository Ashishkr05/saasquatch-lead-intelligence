export type LeadStatus = 'shortlisted' | 'review' | 'rejected'

export interface ScoreItem {
  criterion: string
  points: number
  maximum: number
  explanation: string
}

export interface Lead {
  id: number
  company_name: string
  domain: string | null
  website: string | null
  industry: string | null
  location: string | null
  employee_count: number | null
  year_founded: number | null
  owner_name: string | null
  owner_title: string | null
  email: string | null
  phone: string | null
  description: string | null
  estimated_revenue_m: number | null
  institutionally_backed: boolean
  source: string
  status: LeadStatus
  score: number
  priority: 'high' | 'medium' | 'low'
  score_breakdown: ScoreItem[]
  score_reasons: string[]
  missing_data: string[]
  red_flags: string[]
  acquisition_rationale: string
  outreach_angle: string
  updated_at: string
}

export interface Thesis {
  id: number
  name: string
  industries: string[]
  locations: string[]
  employee_min: number
  employee_max: number
  minimum_years: number
  excluded_keywords: string[]
  exclude_institutionally_backed: boolean
  updated_at: string
}

export interface Metrics {
  total: number
  high_priority: number
  shortlisted: number
  needs_review: number
  average_score: number
  data_completeness: number
}

export interface ImportResult {
  imported: number
  duplicates_skipped: number
  invalid_rows: number
  errors: string[]
}

