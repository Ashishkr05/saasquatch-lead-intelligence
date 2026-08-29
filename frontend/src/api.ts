import type { ImportResult, Lead, LeadStatus, Metrics, Thesis } from './types'

const API_URL = import.meta.env.VITE_API_URL || '/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, options)
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: 'Something went wrong' }))
    throw new Error(body.detail || 'Something went wrong')
  }
  return response.json() as Promise<T>
}

export const api = {
  getLeads: (params: URLSearchParams, signal?: AbortSignal) => request<Lead[]>(`/leads?${params.toString()}`, { signal }),
  getMetrics: (signal?: AbortSignal) => request<Metrics>('/metrics', { signal }),
  getThesis: (signal?: AbortSignal) => request<Thesis>('/thesis', { signal }),
  updateThesis: (thesis: Omit<Thesis, 'id' | 'updated_at'>) => request<Thesis>('/thesis', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(thesis),
  }),
  updateStatus: (id: number, status: LeadStatus) => request<Lead>(`/leads/${id}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  }),
  importCsv: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return request<ImportResult>('/leads/import', { method: 'POST', body: form })
  },
  exportUrl: (status = 'shortlisted') => `${API_URL}/leads-export.csv?status=${status}`,
}
