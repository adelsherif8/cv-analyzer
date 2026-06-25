import { JobProfileCreate, JobProfile, AnalyzeResponse, UploadResponse } from './schemas'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

async function fetchApi<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`
  
  const config: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  }

  try {
    const response = await fetch(url, config)
    
    if (!response.ok) {
      const errorText = await response.text()
      throw new ApiError(response.status, errorText || 'API request failed')
    }

    const data = await response.json()
    return data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`)
  }
}

// Role management
export async function createRole(roleData: JobProfileCreate): Promise<JobProfile> {
  return fetchApi<JobProfile>('/roles', {
    method: 'POST',
    body: JSON.stringify(roleData),
  })
}

export async function getRole(roleId: string): Promise<JobProfile> {
  return fetchApi<JobProfile>(`/roles/${roleId}`)
}

export async function deleteRole(roleId: string): Promise<{ message: string }> {
  return fetchApi<{ message: string }>(`/roles/${roleId}`, {
    method: 'DELETE',
  })
}

export async function listRoles(): Promise<JobProfile[]> {
  return fetchApi<JobProfile[]>('/roles')
}

// File upload
export async function uploadFiles(roleId: string, files: FileList): Promise<UploadResponse[]> {
  const formData = new FormData()
  
  for (let i = 0; i < files.length; i++) {
    formData.append('files', files[i])
  }

  const response = await fetch(`${API_BASE_URL}/upload/${roleId}`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new ApiError(response.status, errorText || 'Upload failed')
  }

  return response.json()
}

export async function listUploadedFiles(roleId: string): Promise<UploadResponse[]> {
  return fetchApi<UploadResponse[]>(`/upload/${roleId}/files`)
}

// Analysis
export async function analyzeRole(roleId: string): Promise<AnalyzeResponse> {
  return fetchApi<AnalyzeResponse>(`/analyze/${roleId}`, {
    method: 'POST',
  })
}

export async function getResults(roleId: string): Promise<AnalyzeResponse> {
  return fetchApi<AnalyzeResponse>(`/analyze/${roleId}/results`)
}

// Candidate actions
export async function updateCandidateStatus(roleId: string, candidateId: string, action: 'favorite' | 'unfavorite' | 'delete' | 'restore'): Promise<{ status: string; message: string }> {
  return fetchApi<{ status: string; message: string }>(`/analyze/${roleId}/candidate-action`, {
    method: 'POST',
    body: JSON.stringify({
      candidate_id: candidateId,
      action: action
    }),
  })
}

// Export
export async function exportCsv(roleId: string): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/analyze/${roleId}/export/csv`)
  
  if (!response.ok) {
    const errorText = await response.text()
    throw new ApiError(response.status, errorText || 'CSV export failed')
  }

  return response.blob()
}

export async function exportPdf(roleId: string): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/analyze/${roleId}/export/pdf`)
  
  if (!response.ok) {
    const errorText = await response.text()
    throw new ApiError(response.status, errorText || 'PDF export failed')
  }

  return response.blob()
}

// Health check
export async function healthCheck(): Promise<{ status: string; model_name: string; data_dir: string }> {
  return fetchApi<{ status: string; model_name: string; data_dir: string }>('/health')
}

// Utility function to download blob as file
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
