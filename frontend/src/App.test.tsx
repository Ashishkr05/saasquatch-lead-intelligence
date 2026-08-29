// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import type { Lead, Metrics, Thesis } from './types'

const lead: Lead = {
  id: 1,
  company_name: 'Acme Mechanical',
  domain: 'acme.example',
  website: 'https://acme.example',
  industry: 'Commercial HVAC',
  location: 'Austin, Texas',
  employee_count: 35,
  year_founded: 2000,
  owner_name: 'Jane Owner',
  owner_title: 'Founder',
  email: 'jane@acme.example',
  phone: '+1-555-555-0100',
  description: 'Recurring commercial maintenance contracts',
  estimated_revenue_m: 8,
  institutionally_backed: false,
  source: 'Synthetic demo',
  status: 'review',
  score: 98,
  priority: 'high',
  score_breakdown: [{ criterion: 'Industry match', points: 25, maximum: 25, explanation: 'Target-industry match' }],
  score_reasons: ['Matches target industry: Commercial HVAC'],
  missing_data: [],
  red_flags: [],
  acquisition_rationale: 'Acme is a strong rules-based fit that still requires diligence.',
  outreach_angle: 'Hi Jane, I came across Acme while researching established HVAC companies in Austin.',
  updated_at: '2026-08-29T00:00:00',
}

const thesis: Thesis = {
  id: 1,
  name: 'Sunbelt Essential Services',
  industries: ['HVAC'],
  locations: ['Texas'],
  employee_min: 10,
  employee_max: 100,
  minimum_years: 10,
  excluded_keywords: ['software'],
  exclude_institutionally_backed: true,
  updated_at: '2026-08-29T00:00:00',
}

const metrics: Metrics = {
  total: 1,
  high_priority: 1,
  shortlisted: 0,
  needs_review: 0,
  average_score: 98,
  data_completeness: 100,
}

function jsonResponse(value: unknown) {
  return new Response(JSON.stringify(value), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('Scout workflow', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input)
      if (url.includes('/leads/') && url.endsWith('/status') && init?.method === 'PATCH') {
        const status = JSON.parse(String(init.body)).status
        return jsonResponse({ ...lead, status })
      }
      if (url.includes('/leads?')) return jsonResponse([lead])
      if (url.endsWith('/metrics')) return jsonResponse(metrics)
      if (url.endsWith('/thesis')) return jsonResponse(thesis)
      if (url.endsWith('/leads/import')) return jsonResponse({ imported: 1, duplicates_skipped: 0, invalid_rows: 0, errors: [] })
      throw new Error(`Unexpected request: ${url}`)
    }))
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText: vi.fn().mockResolvedValue(undefined) },
    })
  })

  afterEach(() => {
    cleanup()
    vi.unstubAllGlobals()
  })

  it('loads the queue and supports the primary dialogs and lead workflow', async () => {
    const user = userEvent.setup()
    render(<App />)

    expect(await screen.findByText('Acme Mechanical')).toBeTruthy()
    expect(screen.getByText('98')).toBeTruthy()

    const thesisButton = screen.getAllByRole('button', { name: /acquisition thesis/i })[0]
    await user.click(thesisButton)
    expect(screen.getByRole('dialog', { name: 'Edit acquisition thesis' })).toBeTruthy()
    await user.keyboard('{Escape}')
    await waitFor(() => expect(screen.queryByRole('dialog', { name: 'Edit acquisition thesis' })).toBeNull())
    expect(document.activeElement).toBe(thesisButton)

    await user.click(screen.getAllByRole('button', { name: /import csv/i })[0])
    expect(screen.getByRole('dialog', { name: 'Import lead CSV' })).toBeTruthy()
    await user.keyboard('{Escape}')
    await waitFor(() => expect(screen.queryByRole('dialog', { name: 'Import lead CSV' })).toBeNull())

    await user.click(screen.getByText('Acme Mechanical'))
    expect(screen.getByRole('dialog', { name: 'Acme Mechanical lead details' })).toBeTruthy()
    await user.click(screen.getByRole('button', { name: 'Add to shortlist' }))
    await waitFor(() => expect(screen.getByRole('button', { name: 'Shortlisted' })).toBeTruthy())
    expect(fetch).toHaveBeenCalledWith('/api/leads/1/status', expect.objectContaining({ method: 'PATCH' }))
  })

  it('opens mobile navigation and makes a table row keyboard-operable', async () => {
    const user = userEvent.setup()
    const { container } = render(<App />)
    await screen.findByText('Acme Mechanical')

    await user.click(screen.getByRole('button', { name: 'Open navigation' }))
    expect(container.querySelector('.sidebar.open')).toBeTruthy()

    const row = screen.getByText('Acme Mechanical').closest('tr')
    expect(row).toBeTruthy()
    fireEvent.keyDown(row!, { key: ' ' })
    expect(screen.getByRole('dialog', { name: 'Acme Mechanical lead details' })).toBeTruthy()
  })
})
