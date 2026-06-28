// Client-side API layer.
//
// The app used to talk to a separate Python FastAPI backend. It now runs as a
// single Next.js app: job profiles + results live in the browser (sessionStorage)
// and the only server call is POST /api/analyze, which parses the CVs, runs RAG
// retrieval, and scores each candidate with the LLM. This keeps the whole thing
// deployable to Vercel as one project with no database.

import { JobProfileCreate, JobProfile, AnalyzeResponse, UploadResponse } from './schemas'

const ROLE_KEY = (id: string) => `cva:role:${id}`
const RESULTS_KEY = (id: string) => `cva:results:${id}`

// File objects can't go in sessionStorage — hold them in memory between the
// upload step and the analyze step (both happen on the same page).
const pendingFiles = new Map<string, File[]>()

function ss(): Storage | null {
  return typeof window !== 'undefined' ? window.sessionStorage : null
}
function uuid(): string {
  return typeof crypto !== 'undefined' && crypto.randomUUID
    ? crypto.randomUUID()
    : Math.random().toString(36).slice(2)
}

// ---------- Role management (client-side) ----------
export async function createRole(roleData: JobProfileCreate): Promise<JobProfile> {
  const profile: JobProfile = {
    ...roleData,
    id: uuid(),
    created_at: new Date().toISOString(),
  }
  ss()?.setItem(ROLE_KEY(profile.id), JSON.stringify(profile))
  return profile
}

export async function getRole(roleId: string): Promise<JobProfile> {
  const raw = ss()?.getItem(ROLE_KEY(roleId))
  if (!raw) throw new Error('Job profile not found. Please create it again.')
  return JSON.parse(raw)
}

export async function deleteRole(roleId: string): Promise<{ message: string }> {
  ss()?.removeItem(ROLE_KEY(roleId))
  ss()?.removeItem(RESULTS_KEY(roleId))
  pendingFiles.delete(roleId)
  return { message: 'deleted' }
}

export async function listRoles(): Promise<JobProfile[]> {
  const store = ss()
  if (!store) return []
  const roles: JobProfile[] = []
  for (let i = 0; i < store.length; i++) {
    const k = store.key(i)
    if (k?.startsWith('cva:role:')) {
      try { roles.push(JSON.parse(store.getItem(k)!)) } catch { /* skip */ }
    }
  }
  return roles
}

// ---------- File upload (held in memory) ----------
export async function uploadFiles(roleId: string, files: FileList): Promise<UploadResponse[]> {
  const arr = Array.from(files)
  pendingFiles.set(roleId, arr)
  return arr.map((f) => ({ candidate_id: uuid(), file_name: f.name, status: 'uploaded' }))
}

export async function listUploadedFiles(roleId: string): Promise<UploadResponse[]> {
  return (pendingFiles.get(roleId) || []).map((f) => ({
    candidate_id: uuid(), file_name: f.name, status: 'uploaded',
  }))
}

// ---------- Analysis (the one server call) ----------
export async function analyzeRole(roleId: string): Promise<AnalyzeResponse> {
  const job = await getRole(roleId)
  const files = pendingFiles.get(roleId) || []
  if (files.length === 0) throw new Error('Please select CV files to analyze.')

  const form = new FormData()
  form.append('job', JSON.stringify(job))
  for (const f of files) form.append('files', f)

  const res = await fetch('/api/analyze', { method: 'POST', body: form })
  if (!res.ok) {
    let detail = 'Analysis failed'
    try { detail = (await res.json()).detail || detail } catch { /* ignore */ }
    throw new Error(detail)
  }
  const fresh: AnalyzeResponse = await res.json()

  // merge with any previously analyzed candidates (incremental uploads)
  const prev = await getResults(roleId)
  const seen = new Set(fresh.results.map((r) => r.file_name))
  const merged = [...fresh.results, ...prev.results.filter((r) => !seen.has(r.file_name))]
  merged.sort((a, b) => b.fit_score - a.fit_score)

  const combined: AnalyzeResponse = { role_id: roleId, results: merged, analyzed_at: fresh.analyzed_at }
  ss()?.setItem(RESULTS_KEY(roleId), JSON.stringify(combined))
  pendingFiles.delete(roleId)
  return combined
}

export async function getResults(roleId: string): Promise<AnalyzeResponse> {
  const raw = ss()?.getItem(RESULTS_KEY(roleId))
  if (!raw) return { role_id: roleId, results: [], analyzed_at: new Date().toISOString() }
  return JSON.parse(raw)
}

// ---------- Candidate actions (client-side) ----------
export async function updateCandidateStatus(
  roleId: string,
  candidateId: string,
  action: 'favorite' | 'unfavorite' | 'delete' | 'restore'
): Promise<{ status: string; message: string }> {
  const data = await getResults(roleId)
  const c = data.results.find((r) => r.candidate_id === candidateId)
  if (c) {
    if (action === 'favorite') c.is_favorite = true
    else if (action === 'unfavorite') c.is_favorite = false
    else if (action === 'delete') c.is_deleted = true
    else if (action === 'restore') c.is_deleted = false
    ss()?.setItem(RESULTS_KEY(roleId), JSON.stringify(data))
  }
  return { status: 'success', message: `Candidate ${action} successfully` }
}

// ---------- Export (client-side CSV) ----------
function resultsToCsv(data: AnalyzeResponse): string {
  const head = ['file_name', 'fit_score', 'years_experience', 'summary', 'suggested_roles', 'red_flags']
  const rows = data.results.map((r) =>
    [
      r.file_name,
      r.fit_score,
      r.years_experience ?? '',
      (r.cv_summary || '').replace(/"/g, '""'),
      (r.suggested_roles || []).join('; '),
      (r.red_flags || []).join('; '),
    ]
      .map((v) => `"${String(v)}"`)
      .join(',')
  )
  return [head.join(','), ...rows].join('\n')
}

export async function exportCsv(roleId: string): Promise<Blob> {
  const data = await getResults(roleId)
  return new Blob([resultsToCsv(data)], { type: 'text/csv' })
}

// PDF export isn't available in the single-app build — return CSV so the button still works
export async function exportPdf(roleId: string): Promise<Blob> {
  return exportCsv(roleId)
}

export async function healthCheck(): Promise<{ status: string; model_name: string; data_dir: string }> {
  return { status: 'ok', model_name: 'gpt-4o-mini', data_dir: 'client' }
}

// Utility: download a blob as a file
export function downloadBlob(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.style.display = 'none'
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  window.URL.revokeObjectURL(url)
  document.body.removeChild(a)
}
