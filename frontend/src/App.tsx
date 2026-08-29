import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  AlertCircle, ArrowDownToLine, ArrowUpRight, BarChart3, BriefcaseBusiness, Building2,
  Check, CheckCircle2, ChevronDown, ChevronRight, CircleAlert, ClipboardCheck, Copy,
  Database, FileUp, Filter, Flag, Gauge, Info, LayoutDashboard, ListFilter, Loader2,
  Mail, MapPin, Menu, Phone, RefreshCw, Search, Settings2, ShieldCheck, SlidersHorizontal,
  Sparkles, Target, ThumbsDown, Upload, Users, X,
} from 'lucide-react'
import { api } from './api'
import { safeWebsiteUrl } from './security'
import type { ImportResult, Lead, LeadStatus, Metrics, Thesis } from './types'

const emptyMetrics: Metrics = { total: 0, high_priority: 0, shortlisted: 0, needs_review: 0, average_score: 0, data_completeness: 0 }

function describeApiError(error: unknown): string {
  return error instanceof Error && error.message !== 'Failed to fetch'
    ? error.message
    : 'Backend is unreachable. Start the API on port 8000, then retry.'
}

function useDialogA11y(onClose: () => void) {
  const dialogRef = useRef<HTMLElement>(null)
  useEffect(() => {
    const dialog = dialogRef.current
    const previouslyFocused = document.activeElement instanceof HTMLElement ? document.activeElement : null
    if (!dialog) return
    const focusable = () => Array.from(dialog.querySelectorAll<HTMLElement>(
      'button:not(:disabled), a[href], input:not(:disabled), textarea:not(:disabled), select:not(:disabled), [tabindex]:not([tabindex="-1"])',
    ))
    focusable()[0]?.focus()
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault()
        onClose()
        return
      }
      if (event.key !== 'Tab') return
      const items = focusable()
      if (!items.length) return
      const first = items[0]
      const last = items[items.length - 1]
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault(); last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault(); first.focus()
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = previousOverflow
      previouslyFocused?.focus()
    }
  }, [onClose])
  return dialogRef
}

function Initials({ name }: { name: string }) {
  const value = name.split(/\s+/).map(part => part[0]).join('').slice(0, 2).toUpperCase()
  const hue = [...name].reduce((sum, char) => sum + char.charCodeAt(0), 0) % 4
  return <span className={`company-logo hue-${hue}`}>{value}</span>
}

function ScoreRing({ score, size = 'medium' }: { score: number; size?: 'small' | 'medium' | 'large' }) {
  const tone = score >= 75 ? 'good' : score >= 50 ? 'warn' : 'poor'
  return (
    <div className={`score-ring ${tone} ${size}`} style={{ '--score': `${score * 3.6}deg` } as React.CSSProperties}>
      <span>{score}</span>
    </div>
  )
}

function StatusPill({ status }: { status: LeadStatus }) {
  const label = status === 'shortlisted' ? 'Shortlisted' : status === 'rejected' ? 'Rejected' : 'In review'
  return <span className={`status-pill ${status}`}><span />{label}</span>
}

function MetricCard({ icon, label, value, detail, accent }: { icon: React.ReactNode; label: string; value: string | number; detail: string; accent: string }) {
  return (
    <article className="metric-card">
      <div className={`metric-icon ${accent}`}>{icon}</div>
      <div className="metric-copy"><span>{label}</span><strong>{value}</strong><small>{detail}</small></div>
    </article>
  )
}

function LeadDetail({ lead, onClose, onStatus }: { lead: Lead; onClose: () => void; onStatus: (status: LeadStatus) => Promise<void> }) {
  const [copyState, setCopyState] = useState<'idle' | 'copied' | 'failed'>('idle')
  const [updating, setUpdating] = useState(false)
  const dialogRef = useDialogA11y(onClose)
  const websiteUrl = safeWebsiteUrl(lead.website)
  const copyOutreach = async () => {
    try {
      await navigator.clipboard.writeText(lead.outreach_angle)
      setCopyState('copied')
    } catch {
      setCopyState('failed')
    }
    window.setTimeout(() => setCopyState('idle'), 1800)
  }
  const changeStatus = async (status: LeadStatus) => {
    if (updating) return
    setUpdating(true)
    try { await onStatus(status) } finally { setUpdating(false) }
  }
  return (
    <div className="drawer-layer">
      <button className="drawer-scrim" onClick={onClose} aria-label="Close lead details" />
      <aside ref={dialogRef} className="lead-drawer" role="dialog" aria-modal="true" aria-label={`${lead.company_name} lead details`}>
        <header className="drawer-header">
          <button className="icon-button" onClick={onClose} aria-label="Close"><X size={19} /></button>
          <span>Lead intelligence</span>
          {websiteUrl ? <a className="icon-button" href={websiteUrl} target="_blank" rel="noreferrer" aria-label="Open company website"><ArrowUpRight size={18} /></a> : <button className="icon-button" disabled aria-label="Company website unavailable"><ArrowUpRight size={18} /></button>}
        </header>

        <div className="drawer-scroll">
          <section className="company-hero">
            <Initials name={lead.company_name} />
            <div><div className="eyebrow">{lead.industry || 'Industry unknown'}</div><h2>{lead.company_name}</h2><p><MapPin size={14} />{lead.location || 'Location unknown'} · {lead.source}</p></div>
            <ScoreRing score={lead.score} size="large" />
          </section>

          <div className="fit-banner">
            <div><Sparkles size={18} /><span><strong>{lead.priority === 'high' ? 'Strong acquisition fit' : lead.priority === 'medium' ? 'Worth a closer look' : 'Low thesis alignment'}</strong><small>Explainable score · no black box</small></span></div>
            <StatusPill status={lead.status} />
          </div>

          <section className="detail-section">
            <div className="section-heading"><div><h3>Why this lead</h3><p>Evidence supporting the score</p></div><Target size={18} /></div>
            <div className="signal-list">
              {lead.score_reasons.length ? lead.score_reasons.map(reason => <div className="signal positive" key={reason}><Check size={15} /><span>{reason}</span></div>) : <div className="empty-inline">No positive thesis signals found.</div>}
            </div>
          </section>

          {(lead.red_flags.length > 0 || lead.missing_data.length > 0) && (
            <section className="detail-section">
              <div className="section-heading"><div><h3>Review before outreach</h3><p>Risks and gaps to verify</p></div><CircleAlert size={18} /></div>
              <div className="signal-list">
                {lead.red_flags.map(flag => <div className="signal negative" key={flag}><Flag size={14} /><span>{flag}</span></div>)}
                {lead.missing_data.map(item => <div className="signal missing" key={item}><Info size={14} /><span>Missing: {item}</span></div>)}
              </div>
            </section>
          )}

          <section className="detail-section">
            <div className="section-heading"><div><h3>Score breakdown</h3><p>Every point is traceable</p></div><Gauge size={18} /></div>
            <div className="score-breakdown">
              {lead.score_breakdown.map(item => (
                <div className="score-row" key={item.criterion}>
                  <div><span>{item.criterion}</span><small>{item.explanation}</small></div>
                  <strong className={item.points < 0 ? 'penalty' : ''}>{item.points > 0 ? '+' : ''}{item.points}<em>{item.maximum ? `/${item.maximum}` : ''}</em></strong>
                </div>
              ))}
            </div>
          </section>

          <section className="detail-section narrative">
            <div className="section-heading"><div><h3>Acquisition rationale</h3><p>Rule-based summary for initial review</p></div><BriefcaseBusiness size={18} /></div>
            <p>{lead.acquisition_rationale}</p>
            <span className="generated-label"><ShieldCheck size={13} /> Deterministic template · Verify before use</span>
          </section>

          <section className="detail-section outreach">
            <div className="section-heading"><div><h3>Suggested outreach angle</h3><p>Personalized from known lead data</p></div><Mail size={18} /></div>
            <div className="outreach-note">{lead.outreach_angle}</div>
            <button className="copy-button" onClick={copyOutreach}>{copyState === 'copied' ? <Check size={15} /> : <Copy size={15} />}{copyState === 'copied' ? 'Copied' : copyState === 'failed' ? 'Copy failed' : 'Copy opener'}</button>
          </section>

          <section className="contact-grid">
            <div><Users size={16} /><span><small>Decision-maker</small><strong>{lead.owner_name || 'Not identified'}</strong><em>{lead.owner_title || '—'}</em></span></div>
            <div><Mail size={16} /><span><small>Email</small><strong>{lead.email || 'Not available'}</strong></span></div>
            <div><Phone size={16} /><span><small>Phone</small><strong>{lead.phone || 'Not available'}</strong></span></div>
            <div><Building2 size={16} /><span><small>Company profile</small><strong>{lead.employee_count ? `${lead.employee_count} employees` : 'Size unknown'}</strong><em>{lead.year_founded ? `Founded ${lead.year_founded}` : 'Age unknown'}</em></span></div>
          </section>
        </div>

        <footer className="drawer-actions">
          <button disabled={updating} className={`secondary-button ${lead.status === 'rejected' ? 'active-reject' : ''}`} onClick={() => void changeStatus('rejected')}><ThumbsDown size={16} /> Reject</button>
          <button disabled={updating} className={`secondary-button ${lead.status === 'review' ? 'active-review' : ''}`} onClick={() => void changeStatus('review')}><ClipboardCheck size={16} /> Review</button>
          <button disabled={updating} className={`primary-button ${lead.status === 'shortlisted' ? 'active' : ''}`} onClick={() => void changeStatus('shortlisted')}>{updating ? <Loader2 className="spin" size={17} /> : <CheckCircle2 size={17} />} {lead.status === 'shortlisted' ? 'Shortlisted' : 'Add to shortlist'}</button>
        </footer>
      </aside>
    </div>
  )
}

function ThesisPanel({ thesis, onClose, onSave }: { thesis: Thesis; onClose: () => void; onSave: (value: Omit<Thesis, 'id' | 'updated_at'>) => Promise<void> }) {
  const dialogRef = useDialogA11y(onClose)
  const [form, setForm] = useState({
    name: thesis.name,
    industries: thesis.industries.join(', '),
    locations: thesis.locations.join(', '),
    employee_min: thesis.employee_min,
    employee_max: thesis.employee_max,
    minimum_years: thesis.minimum_years,
    excluded_keywords: thesis.excluded_keywords.join(', '),
    exclude_institutionally_backed: thesis.exclude_institutionally_backed,
  })
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState('')
  const tags = (value: string) => value.split(',').map(item => item.trim()).filter(Boolean)
  const submit = async (event: React.FormEvent) => {
    event.preventDefault(); setSaving(true); setSaveError('')
    try {
      await onSave({ ...form, industries: tags(form.industries), locations: tags(form.locations), excluded_keywords: tags(form.excluded_keywords) })
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : 'Unable to save the thesis')
    } finally {
      setSaving(false)
    }
  }
  return (
    <div className="drawer-layer">
      <button className="drawer-scrim" onClick={onClose} aria-label="Close thesis settings" />
      <aside ref={dialogRef} className="thesis-drawer" role="dialog" aria-modal="true" aria-label="Edit acquisition thesis">
        <header className="drawer-header"><button className="icon-button" onClick={onClose} aria-label="Close acquisition thesis"><X size={19} /></button><span>Acquisition thesis</span><Target size={18} /></header>
        <form onSubmit={submit}>
          <div className="thesis-intro"><span><SlidersHorizontal size={20} /></span><div><h2>Define what “fit” means</h2><p>Every lead will be rescored against these criteria. Rules stay transparent and repeatable.</p></div></div>
          <label>Thesis name<input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required /></label>
          <label>Target industries<small>Separate multiple values with commas</small><textarea rows={2} value={form.industries} onChange={e => setForm({ ...form, industries: e.target.value })} /></label>
          <label>Target locations<small>State, city, or region names</small><textarea rows={2} value={form.locations} onChange={e => setForm({ ...form, locations: e.target.value })} /></label>
          <div className="field-pair"><label>Min. employees<input type="number" min="1" value={form.employee_min} onChange={e => setForm({ ...form, employee_min: Number(e.target.value) })} /></label><label>Max. employees<input type="number" min="1" value={form.employee_max} onChange={e => setForm({ ...form, employee_max: Number(e.target.value) })} /></label></div>
          <label>Minimum years operating<input type="number" min="0" max="200" value={form.minimum_years} onChange={e => setForm({ ...form, minimum_years: Number(e.target.value) })} /></label>
          <label>Excluded keywords<small>Applied to industry and company description</small><textarea rows={2} value={form.excluded_keywords} onChange={e => setForm({ ...form, excluded_keywords: e.target.value })} /></label>
          <label className="toggle-row"><span><strong>Exclude institutionally backed</strong><small>Penalize PE- or venture-backed companies</small></span><input type="checkbox" checked={form.exclude_institutionally_backed} onChange={e => setForm({ ...form, exclude_institutionally_backed: e.target.checked })} /></label>
          <div className="weight-guide"><div><span>Industry</span><b>25</b></div><div><span>Size</span><b>20</b></div><div><span>Geography</span><b>15</b></div><div><span>Age</span><b>15</b></div><div><span>Owner</span><b>10</b></div><div><span>Contact</span><b>10</b></div><div><span>Data</span><b>5</b></div></div>
          {saveError && <div className="form-error"><AlertCircle size={14} />{saveError}</div>}
          <footer><button type="button" className="secondary-button" onClick={onClose}>Cancel</button><button className="primary-button" disabled={saving}>{saving ? <Loader2 className="spin" size={17} /> : <RefreshCw size={16} />}Save & rescore all leads</button></footer>
        </form>
      </aside>
    </div>
  )
}

function ImportDialog({ onClose, onComplete, onImport }: { onClose: () => void; onComplete: () => void; onImport: (file: File) => Promise<ImportResult> }) {
  const dialogRef = useDialogA11y(onClose)
  const input = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState<ImportResult | null>(null)
  const [importError, setImportError] = useState('')
  const run = async () => {
    if (!file) return
    setBusy(true); setImportError('')
    try {
      setResult(await onImport(file))
    } catch (error) {
      setImportError(error instanceof Error ? error.message : 'Unable to import this CSV')
    } finally {
      setBusy(false)
    }
  }
  return (
    <div className="modal-layer">
      <button className="modal-scrim" onClick={onClose} aria-label="Close import" />
      <section ref={dialogRef} className="import-modal" role="dialog" aria-modal="true" aria-label="Import lead CSV">
        <header><div><span><FileUp size={20} /></span><div><h2>Import company leads</h2><p>Score a list you already sourced</p></div></div><button className="icon-button" onClick={onClose} aria-label="Close import dialog"><X size={18} /></button></header>
        {result ? (
          <div className="import-result"><span><CheckCircle2 size={28} /></span><h3>Import complete</h3><p>{result.imported} leads added and scored against your current thesis.</p><div><b>{result.imported}<small>Imported</small></b><b>{result.duplicates_skipped}<small>Duplicates skipped</small></b><b>{result.invalid_rows}<small>Invalid rows</small></b></div>{result.errors.map(error => <em key={error}>{error}</em>)}<button className="primary-button" onClick={onComplete}>View lead queue</button></div>
        ) : (
          <>
            <button className={`dropzone ${file ? 'has-file' : ''}`} onClick={() => input.current?.click()} onDragOver={e => e.preventDefault()} onDrop={e => { e.preventDefault(); setFile(e.dataTransfer.files[0] || null) }}>
              <input ref={input} type="file" accept=".csv,text/csv" hidden onChange={e => setFile(e.target.files?.[0] || null)} />
              {file ? <><CheckCircle2 size={28} /><strong>{file.name}</strong><small>{(file.size / 1024).toFixed(1)} KB · Ready to import</small></> : <><Upload size={28} /><strong>Drop your CSV here</strong><small>or click to browse · UTF-8, up to 5 MB</small></>}
            </button>
            <div className="csv-help"><h3>Required column</h3><code>company_name</code><h3>Recommended columns</h3><p>domain, website, industry, location, employee_count, year_founded, owner_name, email, phone, description</p><span><ShieldCheck size={15} /> Domains and company/location pairs are deduplicated automatically.</span></div>
            {importError && <div className="form-error import-error"><AlertCircle size={14} />{importError}</div>}
            <footer><button className="secondary-button" onClick={onClose}>Cancel</button><button className="primary-button" onClick={run} disabled={!file || busy}>{busy ? <Loader2 className="spin" size={17} /> : <FileUp size={16} />}Import & score leads</button></footer>
          </>
        )}
      </section>
    </div>
  )
}

export default function App() {
  const [leads, setLeads] = useState<Lead[]>([])
  const [metrics, setMetrics] = useState<Metrics>(emptyMetrics)
  const [thesis, setThesis] = useState<Thesis | null>(null)
  const [selected, setSelected] = useState<Lead | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('all')
  const [priority, setPriority] = useState('all')
  const [sort, setSort] = useState('score_desc')
  const [showThesis, setShowThesis] = useState(false)
  const [showImport, setShowImport] = useState(false)
  const [mobileNav, setMobileNav] = useState(false)
  const [toast, setToast] = useState('')

  const loadLeads = useCallback(async (signal?: AbortSignal) => {
    const params = new URLSearchParams({ sort })
    if (search) params.set('search', search)
    if (status !== 'all') params.set('status', status)
    if (priority !== 'all') params.set('priority', priority)
    setLeads(await api.getLeads(params, signal))
  }, [search, status, priority, sort])

  const loadSummary = useCallback(async (signal?: AbortSignal) => {
    const [nextMetrics, nextThesis] = await Promise.all([api.getMetrics(signal), api.getThesis(signal)])
    setMetrics(nextMetrics); setThesis(nextThesis)
  }, [])

  const loadAll = useCallback(async () => {
    setLoading(true)
    try {
      await Promise.all([loadLeads(), loadSummary()])
      setError('')
    } catch (err) {
      setError(describeApiError(err))
    } finally {
      setLoading(false)
    }
  }, [loadLeads, loadSummary])

  useEffect(() => {
    const controller = new AbortController()
    const timer = window.setTimeout(() => {
      setLoading(true)
      void loadLeads(controller.signal)
        .then(() => setError(''))
        .catch(err => {
          if (!(err instanceof DOMException && err.name === 'AbortError')) setError(describeApiError(err))
        })
        .finally(() => {
          if (!controller.signal.aborted) setLoading(false)
        })
    }, search ? 250 : 0)
    return () => { window.clearTimeout(timer); controller.abort() }
  }, [loadLeads, search])

  useEffect(() => {
    const controller = new AbortController()
    void loadSummary(controller.signal).catch(err => {
      if (!(err instanceof DOMException && err.name === 'AbortError')) setError(describeApiError(err))
    })
    return () => controller.abort()
  }, [loadSummary])

  const notify = (message: string) => { setToast(message); window.setTimeout(() => setToast(''), 2400) }
  const updateStatus = async (lead: Lead, nextStatus: LeadStatus) => {
    try {
      const updated = await api.updateStatus(lead.id, nextStatus)
      setSelected(updated)
      await Promise.all([loadLeads(), api.getMetrics().then(setMetrics)])
      notify(`Moved ${lead.company_name} to ${nextStatus}`)
    } catch (err) {
      notify(err instanceof Error ? err.message : 'Unable to update this lead')
    }
  }
  const saveThesis = async (value: Omit<Thesis, 'id' | 'updated_at'>) => {
    const updated = await api.updateThesis(value); setThesis(updated); await Promise.all([loadLeads(), loadSummary()]); setShowThesis(false); notify('Thesis saved and every lead rescored')
  }
  const importCsv = async (file: File) => { const result = await api.importCsv(file); await Promise.all([loadLeads(), loadSummary()]); return result }

  const showLeadQueue = () => {
    setSearch(''); setStatus('all'); setPriority('all'); setMobileNav(false)
    document.getElementById('lead-queue')?.scrollIntoView({ behavior: 'smooth' })
  }
  const showShortlist = () => {
    setStatus('shortlisted'); setMobileNav(false)
    document.getElementById('lead-queue')?.scrollIntoView({ behavior: 'smooth' })
  }
  const openThesis = () => {
    setMobileNav(false)
    if (thesis) setShowThesis(true)
    else void loadAll()
  }
  const openImport = () => { setMobileNav(false); setShowImport(true) }
  const guardExport = (event: React.MouseEvent<HTMLAnchorElement>) => {
    setMobileNav(false)
    if (error) {
      event.preventDefault()
      notify('Connect the backend before exporting')
    }
  }

  const activeFilters = Number(status !== 'all') + Number(priority !== 'all')
  const thesisLabel = useMemo(() => thesis ? `${thesis.industries.length} industries · ${thesis.locations.length} geographies · ${thesis.employee_min}–${thesis.employee_max} employees` : '', [thesis])

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileNav ? 'open' : ''}`}>
        <div className="brand"><span className="brand-mark"><Target size={19} /></span><span><strong>SCOUT</strong><small>Lead intelligence</small></span><button className="mobile-close" onClick={() => setMobileNav(false)} aria-label="Close navigation"><X size={18} /></button></div>
        <nav>
          <span className="nav-label">Workspace</span>
          <button className={status === 'all' ? 'active' : ''} onClick={showLeadQueue}><LayoutDashboard size={18} /> Lead queue <b>{metrics.total}</b></button>
          <button className={status === 'shortlisted' ? 'active' : ''} onClick={showShortlist}><ClipboardCheck size={18} /> Shortlist <b>{metrics.shortlisted}</b></button>
          <button onClick={openThesis}><Target size={18} /> Acquisition thesis</button>
          <span className="nav-label">Data</span>
          <button onClick={openImport}><Database size={18} /> Import leads</button>
          <a href={api.exportUrl('shortlisted')} onClick={guardExport} aria-disabled={Boolean(error)}><ArrowDownToLine size={18} /> Export shortlist CSV</a>
        </nav>
        <div className="sidebar-card"><Sparkles size={17} /><strong>Decision layer, not another scraper.</strong><p>Prioritize sourced companies by thesis fit and explain every point.</p></div>
        <div className="profile"><span>AK</span><div><strong>Ashish Kumar</strong><small>Acquisition workspace</small></div><ChevronDown size={16} /></div>
      </aside>
      {mobileNav && <button className="mobile-scrim" onClick={() => setMobileNav(false)} aria-label="Close navigation" />}

      <main>
        <header className="topbar"><button className="menu-button" onClick={() => setMobileNav(true)} aria-label="Open navigation"><Menu size={20} /></button><div><span className="live-dot" /> Demo workspace</div><div className="topbar-actions"><button className="ghost-button" onClick={openImport}><FileUp size={16} /> Import CSV</button><a className="primary-button" href={api.exportUrl('shortlisted')} onClick={guardExport} aria-disabled={Boolean(error)}><ArrowDownToLine size={16} /> Export shortlist</a></div></header>

        <div className="page-content">
          <section className="page-heading"><div><span className="eyebrow">Acquisition pipeline</span><h1>Companies worth calling first.</h1><p>Turn sourced leads into an explainable, prioritized outreach queue.</p></div><button className="thesis-chip" onClick={openThesis} disabled={!thesis} title={thesis ? 'Edit acquisition thesis' : 'Thesis is unavailable until the backend connects'}><span><Target size={17} /></span><div><small>Active thesis</small><strong>{thesis?.name || (error ? 'Thesis unavailable' : 'Loading thesis…')}</strong><em>{thesisLabel}</em></div><Settings2 size={17} /></button></section>

          <section className="metrics-grid">
            <MetricCard icon={<Building2 size={20} />} label="Leads analyzed" value={metrics.total} detail="Across all imported sources" accent="navy" />
            <MetricCard icon={<Target size={20} />} label="High-priority fits" value={metrics.high_priority} detail={`${metrics.total ? Math.round(metrics.high_priority / metrics.total * 100) : 0}% of the current pipeline`} accent="green" />
            <MetricCard icon={<ClipboardCheck size={20} />} label="Shortlisted" value={metrics.shortlisted} detail="Ready for focused outreach" accent="blue" />
            <MetricCard icon={<AlertCircle size={20} />} label="Needs verification" value={metrics.needs_review} detail={`${metrics.data_completeness}% profile completeness`} accent="amber" />
          </section>

          <section className="queue-card" id="lead-queue">
            <header className="queue-heading"><div><h2>Lead queue</h2><p>Ranked by acquisition-fit score</p></div><div className="score-legend"><span><i className="good" /> 75+ Strong</span><span><i className="warn" /> 50–74 Review</span><span><i className="poor" /> &lt;50 Low</span></div></header>
            <div className="filterbar">
              <label className="searchbox"><Search size={17} /><input aria-label="Search leads" value={search} onChange={e => setSearch(e.target.value)} placeholder="Search company, industry, or location…" />{search && <button onClick={() => setSearch('')} aria-label="Clear search"><X size={14} /></button>}</label>
              <label className="selectbox"><Filter size={16} /><select aria-label="Filter by fit score" value={priority} onChange={e => setPriority(e.target.value)}><option value="all">All scores</option><option value="high">Strong fit</option><option value="medium">Needs review</option><option value="low">Low fit</option></select><ChevronDown size={14} /></label>
              <label className="selectbox"><ListFilter size={16} /><select aria-label="Filter by workflow status" value={status} onChange={e => setStatus(e.target.value)}><option value="all">All statuses</option><option value="shortlisted">Shortlisted</option><option value="review">In review</option><option value="rejected">Rejected</option></select><ChevronDown size={14} /></label>
              <label className="selectbox sort"><BarChart3 size={16} /><select aria-label="Sort lead queue" value={sort} onChange={e => setSort(e.target.value)}><option value="score_desc">Score: high to low</option><option value="score_asc">Score: low to high</option><option value="company">Company: A–Z</option></select><ChevronDown size={14} /></label>
              {activeFilters > 0 && <button className="clear-filter" onClick={() => { setPriority('all'); setStatus('all') }}>Clear {activeFilters}</button>}
            </div>

            {error ? <div className="state-message error"><AlertCircle size={24} /><h3>Couldn’t load the lead queue</h3><p>{error}</p><button className="secondary-button" onClick={() => void loadAll()} disabled={loading}>{loading ? <Loader2 className="spin" size={15} /> : <RefreshCw size={15} />} {loading ? 'Reconnecting…' : 'Try again'}</button></div> : loading ? <div className="state-message"><Loader2 className="spin" size={25} /><h3>Scoring lead intelligence…</h3></div> : leads.length === 0 ? <div className="state-message"><Search size={25} /><h3>No leads match these filters</h3><p>Clear the filters or import a new lead list.</p></div> : (
              <div className="table-wrap"><table><thead><tr><th>Company</th><th>Profile</th><th>Owner & contact</th><th>Fit score</th><th>Status</th><th aria-label="Actions" /></tr></thead><tbody>{leads.map(lead => (
                <tr key={lead.id} onClick={() => setSelected(lead)} tabIndex={0} onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setSelected(lead) } }}>
                  <td><div className="company-cell"><Initials name={lead.company_name} /><div><strong>{lead.company_name}</strong><span>{lead.domain || 'Domain unavailable'}</span><small className={`source-label ${lead.source === 'Synthetic demo' ? 'synthetic' : 'imported'}`}>{lead.source}</small></div></div></td>
                  <td><div className="profile-cell"><strong>{lead.industry || 'Industry unknown'}</strong><span><MapPin size={12} />{lead.location || 'Location unknown'}{lead.employee_count ? ` · ${lead.employee_count} employees` : ''}</span></div></td>
                  <td><div className="contact-cell"><strong>{lead.owner_name || 'Owner not identified'}</strong><span>{lead.email ? <><Mail size={12} /> Email</> : <><CircleAlert size={12} /> Missing email</>}{lead.phone && <><Phone size={12} /> Phone</>}</span></div></td>
                  <td><div className="score-cell"><ScoreRing score={lead.score} size="small" /><div><strong>{lead.priority === 'high' ? 'Strong fit' : lead.priority === 'medium' ? 'Review' : 'Low fit'}</strong><span>{lead.score_reasons.length} positive signals</span></div></div></td>
                  <td><StatusPill status={lead.status} /></td>
                  <td><button className="row-action" onClick={e => { e.stopPropagation(); setSelected(lead) }} aria-label={`View ${lead.company_name}`}><ChevronRight size={18} /></button></td>
                </tr>
              ))}</tbody></table></div>
            )}
            <footer className="queue-footer"><span>Showing <strong>{leads.length}</strong> prioritized leads</span><span><ShieldCheck size={14} /> Rules-based scoring · Last rescored {thesis ? new Date(thesis.updated_at).toLocaleDateString() : 'today'}</span></footer>
          </section>
          <footer className="ethics-note"><ShieldCheck size={17} /><div><strong>Built for responsible acquisition outreach</strong><p>Use permitted data sources, respect opt-outs, and verify generated language before contacting an owner.</p></div></footer>
        </div>
      </main>

      {selected && <LeadDetail lead={selected} onClose={() => setSelected(null)} onStatus={statusValue => updateStatus(selected, statusValue)} />}
      {showThesis && thesis && <ThesisPanel thesis={thesis} onClose={() => setShowThesis(false)} onSave={saveThesis} />}
      {showImport && <ImportDialog onClose={() => setShowImport(false)} onComplete={() => { setShowImport(false); showLeadQueue() }} onImport={importCsv} />}
      {toast && <div className="toast" role="status" aria-live="polite"><CheckCircle2 size={17} />{toast}</div>}
    </div>
  )
}
