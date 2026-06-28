import { NextRequest, NextResponse } from 'next/server'
import { analyzeCV, type JobProfile } from '../../../lib/server/analyze'

// pdf-parse + mammoth need the Node runtime (not edge)
export const runtime = 'nodejs'
export const maxDuration = 60

// POST /api/analyze  (multipart)
//   field "job"   -> JSON string of the JobProfile
//   field "files" -> one or more CV files (pdf/docx/txt)
// returns { role_id, results: CandidateResult[], analyzed_at }
export async function POST(req: NextRequest) {
  try {
    const form = await req.formData()

    const jobRaw = form.get('job')
    if (typeof jobRaw !== 'string') {
      return NextResponse.json({ detail: 'Missing job profile' }, { status: 400 })
    }
    const job = JSON.parse(jobRaw) as JobProfile
    if (!job?.title || !Array.isArray(job?.required_skills) || job.required_skills.length === 0) {
      return NextResponse.json({ detail: 'Invalid job profile' }, { status: 400 })
    }

    const files = form.getAll('files').filter((f): f is File => f instanceof File)
    if (files.length === 0) {
      return NextResponse.json({ detail: 'No files uploaded' }, { status: 400 })
    }

    const results = await Promise.all(
      files.map(async (file) => {
        const buf = Buffer.from(await file.arrayBuffer())
        return analyzeCV(file.name, buf, job)
      })
    )

    results.sort((a, b) => b.fit_score - a.fit_score)

    return NextResponse.json({
      role_id: job.id || 'role',
      results,
      analyzed_at: new Date().toISOString(),
    })
  } catch (e) {
    return NextResponse.json(
      { detail: `Analysis failed: ${(e as Error).message}` },
      { status: 500 }
    )
  }
}
