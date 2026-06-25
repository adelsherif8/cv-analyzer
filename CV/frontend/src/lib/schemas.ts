import { z } from 'zod'

// Skill weight schema
export const SkillWeightSchema = z.object({
  name: z.string().min(1, 'Skill name is required'),
  weight: z.number().min(0).max(1),
})

// Candidate details schema
export const CandidateDetailsSchema = z.object({
  name: z.string().optional(),
  email: z.string().optional(),
  phone: z.string().optional(),
  location: z.string().optional(),
  linkedin: z.string().optional(),
  github: z.string().optional(),
  portfolio: z.string().optional(),
  other_links: z.array(z.string()).optional(),
})

// Job profile schemas
export const JobProfileCreateSchema = z.object({
  title: z.string().min(1, 'Title is required'),
  description: z.string().min(1, 'Description is required'),
  required_skills: z.array(SkillWeightSchema).min(1, 'At least one skill is required'),
})

export const JobProfileSchema = JobProfileCreateSchema.extend({
  id: z.string(),
  created_at: z.string(),
})

// Candidate result schemas
export const CandidateResultSchema = z.object({
  candidate_id: z.string(),
  file_name: z.string(),
  fit_score: z.number().min(0).max(10),
  why: z.array(z.string()),
  cv_summary: z.string(),
  suggested_roles: z.array(z.string()),
  red_flags: z.array(z.string()).nullable().optional(),
  years_experience: z.number().optional(),
  last_role: z.string().optional(),
  is_favorite: z.boolean().optional().default(false),
  is_deleted: z.boolean().optional().default(false),
  candidate_details: CandidateDetailsSchema.optional(),
  skill_analysis: z.record(z.object({
    score: z.number().min(0).max(10),
    evidence: z.array(z.string()),
    years_experience: z.number().optional(),
  })).optional(),
})

export const AnalyzeResponseSchema = z.object({
  role_id: z.string(),
  results: z.array(CandidateResultSchema),
  analyzed_at: z.string(),
})

export const UploadResponseSchema = z.object({
  candidate_id: z.string(),
  file_name: z.string(),
  status: z.string(),
})

// Type exports
export type SkillWeight = z.infer<typeof SkillWeightSchema>
export type JobProfileCreate = z.infer<typeof JobProfileCreateSchema>
export type JobProfile = z.infer<typeof JobProfileSchema>
export type CandidateDetails = z.infer<typeof CandidateDetailsSchema>
export type CandidateResult = z.infer<typeof CandidateResultSchema>
export type AnalyzeResponse = z.infer<typeof AnalyzeResponseSchema>
export type UploadResponse = z.infer<typeof UploadResponseSchema>
