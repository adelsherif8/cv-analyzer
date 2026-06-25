import { type ClassValue, clsx } from "clsx"

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs)
}

export function formatScore(score: number): string {
  return score.toFixed(1)
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

export function validateFileType(file: File): boolean {
  const allowedTypes = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain'
  ]
  
  const allowedExtensions = ['.pdf', '.doc', '.docx', '.txt']
  const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase()
  
  return allowedTypes.includes(file.type) || allowedExtensions.includes(fileExtension)
}

export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength - 3) + '...'
}

export function getScoreColor(score: number): string {
  if (score >= 8) return 'text-green-600'
  if (score >= 6) return 'text-yellow-600'  
  if (score >= 4) return 'text-orange-600'
  return 'text-red-600'
}

export function getScoreBadgeColor(score: number): string {
  if (score >= 8) return 'bg-green-100 text-green-800'
  if (score >= 6) return 'bg-yellow-100 text-yellow-800'
  if (score >= 4) return 'bg-orange-100 text-orange-800'
  return 'bg-red-100 text-red-800'
}
