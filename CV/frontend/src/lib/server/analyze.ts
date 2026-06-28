// Server-side CV analysis — ported from the Python FastAPI backend so the whole
// app runs as a single Next.js deployment (no separate Python service).
//
// Flow per CV: extract text -> retrieve the passages most relevant to the role
// (lightweight RAG) -> one structured LLM call that scores the candidate and
// writes a grounded summary. Falls back to a deterministic keyword scorer when
// no OPENAI_API_KEY is set, so the app is fully demoable offline.

import OpenAI from 'openai'
// pdf-parse + mammoth are imported lazily inside extractText() — importing them
// at module top can crash the serverless function at cold start on Vercel.

export interface SkillWeight {
  name: string
  weight: number
  critical?: boolean
}
export interface JobProfile {
  id?: string
  title: string
  description: string
  required_skills: SkillWeight[]
}
export interface CandidateResult {
  candidate_id: string
  file_name: string
  fit_score: number
  why: string[]
  cv_summary: string
  suggested_roles: string[]
  red_flags: string[]
  years_experience: number | null
  last_role: string | null
  candidate_details: Record<string, unknown> | null
  skill_analysis: Record<string, { score: number; evidence: string[]; years_experience?: number | null }>
  retrieved_context: string[]
  retrieval_mode: string
  is_favorite: boolean
  is_deleted: boolean
}

const MODEL = 'gpt-4o-mini'

// ---------- text extraction ----------
export async function extractText(fileName: string, buffer: Buffer): Promise<string> {
  const lower = fileName.toLowerCase()
  if (lower.endsWith('.pdf')) {
    // unpdf ships a serverless-ready pdf.js build (works on Vercel functions)
    const { extractText, getDocumentProxy } = await import('unpdf')
    const pdf = await getDocumentProxy(new Uint8Array(buffer))
    const { text } = await extractText(pdf, { mergePages: true })
    return (Array.isArray(text) ? text.join('\n') : text || '').trim()
  }
  if (lower.endsWith('.docx') || lower.endsWith('.doc')) {
    const mammoth = (await import('mammoth')).default
    const res = await mammoth.extractRawText({ buffer })
    return (res.value || '').trim()
  }
  // txt / rtf / fallback
  return buffer.toString('utf-8').trim()
}

// ---------- lightweight RAG retrieval (keyword overlap, no extra API) ----------
function tokenize(s: string): string[] {
  return (s.toLowerCase().match(/[a-z0-9+#.]+/g) || []).filter((t) => t.length > 1)
}

export function retrievePassages(cvText: string, query: string, k = 4): { passages: string[]; mode: string } {
  // split into reasonably sized chunks on blank lines / single newlines
  const raw = cvText
    .split(/\n{2,}|\r\n\r\n/)
    .flatMap((b) => (b.length > 400 ? b.split(/\n/) : [b]))
    .map((c) => c.replace(/\s+/g, ' ').trim())
    .filter((c) => c.length > 25)
  if (raw.length === 0) return { passages: [], mode: 'none' }

  const qTerms = new Set(tokenize(query))
  const scored = raw.map((chunk) => {
    const terms = tokenize(chunk)
    let overlap = 0
    for (const t of terms) if (qTerms.has(t)) overlap++
    // normalize a little by length so long chunks don't always win
    return { chunk, score: overlap / Math.sqrt(terms.length + 1) }
  })
  scored.sort((a, b) => b.score - a.score)
  const top = scored.filter((s) => s.score > 0).slice(0, k).map((s) => s.chunk)
  // if nothing overlapped, fall back to the first few chunks
  const passages = top.length ? top : raw.slice(0, k)
  return { passages, mode: 'keyword' }
}

// ---------- helpers shared by LLM + mock ----------
function estimateYears(cv: string): number {
  const m = cv.match(/(\d+)\+?\s*years?/i)
  if (m) return Math.min(40, parseInt(m[1], 10))
  // count 20xx years mentioned, range as a rough proxy
  const years = (cv.match(/\b(19|20)\d{2}\b/g) || []).map(Number)
  if (years.length >= 2) return Math.max(0, Math.min(30, Math.max(...years) - Math.min(...years)))
  return 0
}

// ---------- LLM analysis ----------
async function analyzeWithLLM(
  client: OpenAI,
  cvText: string,
  job: JobProfile,
  passages: string[]
): Promise<Partial<CandidateResult> & { skills?: { name: string; score: number; evidence: string[] }[] }> {
  const skillList = job.required_skills.map((s) => `${s.name} (weight ${s.weight})`).join(', ')
  const grounding = passages.length ? passages.map((p) => `- ${p}`).join('\n') : cvText.slice(0, 1500)

  const prompt = `You are an expert technical recruiter. Score this candidate against the job and return ONLY JSON.

JOB
Title: ${job.title}
Description: ${job.description}
Required skills (with weights): ${skillList}

MOST RELEVANT CV PASSAGES (ground every claim in these):
${grounding}

FULL CV (for reference, may be truncated):
${cvText.slice(0, 4000)}

Return JSON exactly in this shape:
{
  "candidate_details": {"name": str|null, "email": str|null, "phone": str|null, "location": str|null, "linkedin": str|null, "github": str|null, "portfolio": str|null},
  "years_experience": number,
  "last_role": str,
  "fit_score": number,            // 0-10, weighted by the skill weights above
  "summary": str,                 // 2-3 sentence executive summary, grounded in the passages
  "why": [str],                   // 3-4 short bullet reasons for the score
  "suggested_roles": [str],       // 2-3 roles this candidate fits
  "red_flags": [str],             // concerns, or [] if none
  "skills": [ {"name": str, "score": number, "evidence": [str]} ]  // one entry per required skill, score 0-10
}`

  const resp = await client.chat.completions.create({
    model: MODEL,
    messages: [
      { role: 'system', content: 'You are an executive recruiter. Return only valid JSON, no prose.' },
      { role: 'user', content: prompt },
    ],
    temperature: 0.2,
    response_format: { type: 'json_object' },
    max_tokens: 900,
  })
  return JSON.parse(resp.choices[0].message.content || '{}')
}

// ---------- deterministic mock (no API key) ----------
function analyzeWithMock(cvText: string, job: JobProfile, passages: string[]) {
  const tokens = new Set(tokenize(cvText))
  const skills = job.required_skills.map((s) => {
    const parts = tokenize(s.name)
    const hits = parts.filter((p) => tokens.has(p)).length
    const ratio = parts.length ? hits / parts.length : 0
    const score = ratio >= 1 ? 8 : ratio > 0 ? 5 : 2
    const evidence = passages.filter((p) => parts.some((t) => p.toLowerCase().includes(t))).slice(0, 2)
    return { name: s.name, score, evidence }
  })
  const totalW = job.required_skills.reduce((a, s) => a + (s.weight || 0), 0) || 1
  const fit =
    job.required_skills.reduce((a, s, i) => a + skills[i].score * (s.weight || 0), 0) / totalW
  const years = estimateYears(cvText)
  return {
    candidate_details: null,
    years_experience: years,
    last_role: 'Professional',
    fit_score: Math.round(fit * 10) / 10,
    summary: `Candidate with ~${years} years of experience. Matches ${skills.filter((s) => s.score >= 5).length}/${skills.length} required skills for ${job.title}. (Demo mode — set OPENAI_API_KEY for full AI analysis.)`,
    why: skills.map((s) => `${s.name}: ${s.score}/10`),
    suggested_roles: [job.title],
    red_flags: [] as string[],
    skills,
  }
}

// ---------- public entry ----------
export async function analyzeCV(
  fileName: string,
  buffer: Buffer,
  job: JobProfile
): Promise<CandidateResult> {
  const candidate_id = crypto.randomUUID()
  let cvText = ''
  try {
    cvText = await extractText(fileName, buffer)
  } catch (e) {
    return errorResult(candidate_id, fileName, `Could not read file: ${(e as Error).message}`)
  }
  if (!cvText || cvText.length < 20) {
    return errorResult(candidate_id, fileName, 'No readable text found in this file.')
  }

  const query = `${job.title}. Required skills: ${job.required_skills.map((s) => s.name).join(', ')}`
  const { passages, mode } = retrievePassages(cvText, query, 4)

  const key = process.env.OPENAI_API_KEY
  let a: any
  try {
    a = key
      ? await analyzeWithLLM(new OpenAI({ apiKey: key }), cvText, job, passages)
      : analyzeWithMock(cvText, job, passages)
  } catch (e) {
    // if the LLM call fails, degrade gracefully to the mock scorer
    a = analyzeWithMock(cvText, job, passages)
    a.red_flags = [...(a.red_flags || []), 'AI analysis unavailable — showed keyword-based scores']
  }

  const skill_analysis: CandidateResult['skill_analysis'] = {}
  for (const s of a.skills || []) {
    skill_analysis[s.name] = {
      score: clamp(s.score),
      evidence: Array.isArray(s.evidence) ? s.evidence : [],
      years_experience: a.years_experience ?? null,
    }
  }

  const fit = clamp(a.fit_score ?? 0)
  const matchPct = Math.round(fit * 10)
  return {
    candidate_id,
    file_name: fileName,
    fit_score: fit,
    why: [`Score: ${fit}/10 (${matchPct}% match)`, ...(a.why || []).slice(0, 4)],
    cv_summary: a.summary || 'Candidate analyzed.',
    suggested_roles: a.suggested_roles?.length ? a.suggested_roles : [job.title],
    red_flags: a.red_flags || [],
    years_experience: a.years_experience ?? null,
    last_role: a.last_role ?? null,
    candidate_details: a.candidate_details ?? null,
    skill_analysis,
    retrieved_context: passages,
    retrieval_mode: mode,
    is_favorite: false,
    is_deleted: false,
  }
}

function clamp(n: number): number {
  if (typeof n !== 'number' || isNaN(n)) return 0
  return Math.max(0, Math.min(10, Math.round(n * 10) / 10))
}

function errorResult(id: string, fileName: string, msg: string): CandidateResult {
  return {
    candidate_id: id,
    file_name: fileName,
    fit_score: 0,
    why: [msg],
    cv_summary: 'Unable to analyze this CV.',
    suggested_roles: [],
    red_flags: [msg],
    years_experience: null,
    last_role: null,
    candidate_details: null,
    skill_analysis: {},
    retrieved_context: [],
    retrieval_mode: 'none',
    is_favorite: false,
    is_deleted: false,
  }
}
