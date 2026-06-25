'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { Upload, Download, FileText, Users, Star, Heart, Trash2, ChevronDown, ChevronUp, Filter, SortAsc } from 'lucide-react'
import { JobProfile, CandidateResult, AnalyzeResponse } from '../../../lib/schemas'
import { getRole, uploadFiles, analyzeRole, getResults, updateCandidateStatus } from '../../../lib/api'

export default function RolePage() {
  const params = useParams()
  const router = useRouter()
  const roleId = params.id as string
  
  const [role, setRole] = useState<JobProfile | null>(null)
  const [candidates, setCandidates] = useState<CandidateResult[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [expandedCandidate, setExpandedCandidate] = useState<string | null>(null)
  const [filterFavorites, setFilterFavorites] = useState(false)
  const [sortBy, setSortBy] = useState<'score' | 'name' | 'experience'>('score')

  useEffect(() => {
    loadRole()
    loadExistingResults()
  }, [roleId])

  const loadRole = async () => {
    try {
      setIsLoading(true)
      const roleData = await getRole(roleId)
      setRole(roleData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load role')
    } finally {
      setIsLoading(false)
    }
  }

  const loadExistingResults = async () => {
    try {
      const results = await getResults(roleId)
      setCandidates(results.results)
    } catch (err) {
      // Ignore errors for existing results - they may not exist yet
      console.log('No existing results found')
    }
  }

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSelectedFiles(event.target.files)
    setError(null)
  }

  const handleUploadAndAnalyze = async () => {
    if (!selectedFiles || selectedFiles.length === 0) {
      setError('Please select CV files to upload')
      return
    }

    try {
      setIsAnalyzing(true)
      setError(null)
      
      // Upload files
      await uploadFiles(roleId, selectedFiles)
      setUploadProgress(50)
      
      // Analyze files
      const analysisResult = await analyzeRole(roleId)
      setCandidates(analysisResult.results)
      setUploadProgress(100)
      
      // Reset file input
      setSelectedFiles(null)
      const fileInput = document.getElementById('file-upload') as HTMLInputElement
      if (fileInput) fileInput.value = ''
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze files')
    } finally {
      setIsAnalyzing(false)
      setUploadProgress(0)
    }
  }

  const getRankColor = (rank: number) => {
    if (rank <= 3) return 'text-green-600 bg-green-100'
    if (rank <= 6) return 'text-yellow-600 bg-yellow-100'
    return 'text-red-600 bg-red-100'
  }

  const getScoreColor = (score: number) => {
    if (score >= 8) return 'text-green-600'
    if (score >= 6) return 'text-yellow-600'
    return 'text-red-600'
  }

  const handleCandidateAction = async (candidateId: string, action: 'favorite' | 'unfavorite' | 'delete' | 'restore') => {
    try {
      await updateCandidateStatus(roleId, candidateId, action)
      
      // Update local state
      setCandidates(prev => prev.map(candidate => 
        candidate.candidate_id === candidateId 
          ? {
              ...candidate,
              is_favorite: action === 'favorite' ? true : action === 'unfavorite' ? false : candidate.is_favorite,
              is_deleted: action === 'delete' ? true : action === 'restore' ? false : candidate.is_deleted
            }
          : candidate
      ))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update candidate status')
    }
  }

  const filteredAndSortedCandidates = candidates
    .filter(candidate => !candidate.is_deleted)
    .filter(candidate => !filterFavorites || candidate.is_favorite)
    .sort((a, b) => {
      switch (sortBy) {
        case 'score':
          return (b.fit_score || 0) - (a.fit_score || 0)
        case 'name':
          return a.file_name.localeCompare(b.file_name)
        case 'experience':
          return (b.years_experience || 0) - (a.years_experience || 0)
        default:
          return 0
      }
    })

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-center">
          <div className="mx-auto border-4 border-t-blue-600 border-blue-200 rounded-full w-8 h-8 animate-spin"></div>
          <p className="mt-2 text-gray-600">Loading role...</p>
        </div>
      </div>
    )
  }

  if (error && !role) {
    return (
      <div className="mx-auto px-4 py-12 container">
        <div className="bg-red-50 p-6 border border-red-200 rounded-lg text-center">
          <div className="mx-auto mb-4 w-12 h-12 text-red-600">
            <FileText className="w-full h-full" />
          </div>
          <h2 className="mb-2 font-semibold text-red-800 text-lg">Role Not Found</h2>
          <p className="mb-4 text-red-600">{error}</p>
          <button
            onClick={() => router.push('/')}
            className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded-lg font-medium text-white transition-colors"
          >
            Back to Home
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto px-4 py-8 container">
      {/* Role Header */}
      <div className="bg-white shadow-sm mb-8 p-6 border rounded-lg">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h1 className="mb-2 font-bold text-gray-900 text-2xl">{role?.title}</h1>
            <p className="text-gray-600">{role?.description}</p>
          </div>
          <button
            onClick={() => router.push('/role/new')}
            className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg font-medium text-white transition-colors"
          >
            Create New Role
          </button>
        </div>
        
        {/* Required Skills */}
        <div>
          <h3 className="mb-3 font-semibold text-gray-900">Required Skills</h3>
          <div className="flex flex-wrap gap-2">
            {role?.required_skills.map((skill, index) => (
              <div key={index} className="flex items-center bg-blue-50 px-3 py-1 rounded-full text-sm">
                <span className="font-medium text-blue-900">{skill.name}</span>
                <span className="ml-2 text-blue-600">({Math.round(skill.weight * 100)}%)</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Upload Section */}
      <div className="bg-white shadow-sm mb-8 p-6 border rounded-lg">
        <h2 className="flex items-center mb-4 font-bold text-gray-900 text-xl">
          <Upload className="mr-2 w-5 h-5" />
          Upload & Analyze CVs
        </h2>
        
        <div className="space-y-4">
          <div>
            <label htmlFor="file-upload" className="block mb-2 font-medium text-gray-700 text-sm">
              Select CV files (PDF, DOC, DOCX, TXT, RTF)
            </label>
            <input
              id="file-upload"
              type="file"
              multiple
              accept=".pdf,.doc,.docx,.txt,.rtf,.odt"
              onChange={handleFileChange}
              className="block hover:file:bg-blue-100 file:bg-blue-50 file:mr-4 file:px-4 file:py-2 border-gray-300 file:border-0 rounded-lg file:rounded-lg w-full file:font-medium file:text-blue-700 text-sm transition-colors"
            />
          </div>
          
          {selectedFiles && selectedFiles.length > 0 && (
            <div className="bg-gray-50 p-3 rounded-lg">
              <p className="font-medium text-gray-700 text-sm">Selected files:</p>
              <ul className="mt-1 text-gray-600 text-sm">
                {Array.from(selectedFiles).map((file, index) => (
                  <li key={`${file.name}-${file.size}-${index}`} className="flex items-center">
                    <FileText className="mr-1 w-4 h-4" />
                    {file.name}
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {error && (
            <div className="bg-red-50 p-3 border border-red-200 rounded-lg">
              <p className="text-red-600 text-sm">{error}</p>
            </div>
          )}
          
          <button
            onClick={handleUploadAndAnalyze}
            disabled={!selectedFiles || isAnalyzing}
            className="flex items-center bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 px-6 py-2 rounded-lg font-medium text-white transition-colors"
          >
            {isAnalyzing ? (
              <>
                <div className="mr-2 border-2 border-white border-t-transparent rounded-full w-4 h-4 animate-spin"></div>
                Analyzing...
              </>
            ) : (
              <>
                <Upload className="mr-2 w-4 h-4" />
                Upload & Analyze
              </>
            )}
          </button>
          
          {uploadProgress > 0 && uploadProgress < 100 && (
            <div className="bg-gray-200 rounded-full w-full h-2">
              <div 
                className="bg-blue-600 rounded-full h-2 transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              ></div>
            </div>
          )}
        </div>
      </div>

      {/* Results Section */}
      {candidates.length > 0 && (
        <div className="bg-white shadow-sm p-6 border rounded-lg">
          <div className="flex justify-between items-center mb-6">
            <h2 className="flex items-center font-bold text-gray-900 text-xl">
              <Users className="mr-2 w-5 h-5" />
              Analysis Results ({filteredAndSortedCandidates.length} candidates)
            </h2>
            <div className="flex gap-3">
              {/* Filter and Sort Controls */}
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setFilterFavorites(!filterFavorites)}
                  className={`flex items-center px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                    filterFavorites 
                      ? 'bg-red-100 text-red-700 hover:bg-red-200' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  <Heart className={`mr-1 w-4 h-4 ${filterFavorites ? 'fill-current' : ''}`} />
                  {filterFavorites ? 'Show All' : 'Favorites Only'}
                </button>
                
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as 'score' | 'name' | 'experience')}
                  className="bg-gray-100 px-3 py-1 border border-gray-300 rounded-lg text-sm"
                >
                  <option value="score">Sort by Score</option>
                  <option value="name">Sort by Name</option>
                  <option value="experience">Sort by Experience</option>
                </select>
              </div>
              
              <button className="flex items-center bg-green-600 hover:bg-green-700 px-4 py-2 rounded-lg font-medium text-white transition-colors">
                <Download className="mr-2 w-4 h-4" />
                Export Results
              </button>
            </div>
          </div>
          
          <div className="space-y-4">
            {filteredAndSortedCandidates.map((candidate, index) => (
              <div key={`${candidate.file_name}-${candidate.fit_score}-${index}`} className="hover:bg-gray-50 p-4 border rounded-lg transition-colors">
                <div className="flex justify-between items-start mb-3">
                  <div className="flex flex-1 items-center">
                    <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold mr-3 ${getRankColor(index + 1)}`}>
                      {index + 1}
                    </span>
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900">
                        {candidate.candidate_details?.name || candidate.file_name}
                      </h3>
                      {candidate.candidate_details?.email && (
                        <p className="text-blue-600 text-sm hover:underline">
                          <a href={`mailto:${candidate.candidate_details.email}`}>
                            {candidate.candidate_details.email}
                          </a>
                        </p>
                      )}
                      <div className="flex items-center mt-1">
                        <Star className="mr-1 w-4 h-4 text-yellow-500" />
                        <span className={`font-bold ${getScoreColor(candidate.fit_score || 0)}`}>
                          {candidate.fit_score || 0}/10
                        </span>
                        {candidate.years_experience && (
                          <span className="ml-3 text-gray-600 text-sm">
                            {candidate.years_experience} years experience
                          </span>
                        )}
                        {candidate.candidate_details?.phone && (
                          <span className="ml-3 text-gray-600 text-sm">
                            📱 {candidate.candidate_details.phone}
                          </span>
                        )}
                        {candidate.candidate_details?.location && (
                          <span className="ml-3 text-gray-600 text-sm">
                            📍 {candidate.candidate_details.location}
                          </span>
                        )}
                      </div>
                      
                      {/* Contact Links */}
                      {(candidate.candidate_details?.linkedin || candidate.candidate_details?.github || candidate.candidate_details?.portfolio) && (
                        <div className="flex items-center gap-3 mt-2">
                          {candidate.candidate_details?.linkedin && (
                            <a
                              href={candidate.candidate_details.linkedin}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex items-center text-blue-600 hover:text-blue-800 text-sm"
                            >
                              💼 LinkedIn
                            </a>
                          )}
                          {candidate.candidate_details?.github && (
                            <a
                              href={candidate.candidate_details.github}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex items-center text-gray-800 hover:text-gray-900 text-sm"
                            >
                              🐙 GitHub
                            </a>
                          )}
                          {candidate.candidate_details?.portfolio && (
                            <a
                              href={candidate.candidate_details.portfolio}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex items-center text-green-600 hover:text-green-800 text-sm"
                            >
                              🌐 Portfolio
                            </a>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {/* Action Buttons */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleCandidateAction(candidate.candidate_id, candidate.is_favorite ? 'unfavorite' : 'favorite')}
                      className={`flex items-center px-2 py-1 rounded text-sm transition-colors ${
                        candidate.is_favorite
                          ? 'bg-red-100 text-red-700 hover:bg-red-200'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      <Heart className={`w-4 h-4 ${candidate.is_favorite ? 'fill-current' : ''}`} />
                    </button>
                    
                    <button
                      onClick={() => setExpandedCandidate(expandedCandidate === candidate.candidate_id ? null : candidate.candidate_id)}
                      className="flex items-center bg-blue-100 hover:bg-blue-200 px-2 py-1 rounded text-blue-700 text-sm transition-colors"
                    >
                      {expandedCandidate === candidate.candidate_id ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                    
                    <button
                      onClick={() => handleCandidateAction(candidate.candidate_id, 'delete')}
                      className="flex items-center bg-red-100 hover:bg-red-200 px-2 py-1 rounded text-red-700 text-sm transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <div>
                    <h4 className="font-medium text-gray-700 text-sm">Summary</h4>
                    <p className="text-gray-600 text-sm">{candidate.cv_summary}</p>
                  </div>
                  
                  <div>
                    <h4 className="font-medium text-gray-700 text-sm">Key Reasons</h4>
                    <div className="space-y-3 mt-2">
                      {candidate.why?.map((reason, reasonIndex) => (
                        <div key={reasonIndex} className="pl-3 border-gray-200 border-l-2">
                          {reason.split('\n').map((line, lineIndex) => {
                            // Check if line contains HTML span for color coding
                            if (line.includes('<span class=')) {
                              // Extract the percentage and color class
                              const spanMatch = line.match(/<span class='([^']+)'[^>]*>([^<]+)<\/span>/);
                              if (spanMatch) {
                                const colorClass = spanMatch[1];
                                const percentage = spanMatch[2];
                                const beforeSpan = line.substring(0, line.indexOf('<span'));
                                const afterSpan = line.substring(line.indexOf('</span>') + 7);
                                
                                return (
                                  <div key={lineIndex} className="text-gray-600 text-sm">
                                    {beforeSpan}
                                    <span className={`font-bold ${
                                      colorClass.includes('green') ? 'text-green-600' :
                                      colorClass.includes('orange') ? 'text-orange-500' :
                                      'text-red-600'
                                    }`}>
                                      {percentage}
                                    </span>
                                    {afterSpan}
                                  </div>
                                );
                              }
                            }
                            
                            // Handle bold headers (lines with **)
                            if (line.includes('**') && lineIndex === 0) {
                              return (
                                <h5 key={lineIndex} className="font-bold text-gray-800 text-sm">
                                  {line.replace(/\*\*/g, '')}
                                </h5>
                              );
                            }
                            
                            // Handle bullet points
                            if (line.startsWith('• ')) {
                              return (
                                <div key={lineIndex} className="ml-2 text-gray-500 text-xs">
                                  {line}
                                </div>
                              );
                            }
                            
                            // Handle regular lines
                            if (line.trim()) {
                              return (
                                <div key={lineIndex} className="text-gray-600 text-sm">
                                  {line}
                                </div>
                              );
                            }
                            
                            return null;
                          })}
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  {/* Expanded Skill Analysis */}
                  {expandedCandidate === candidate.candidate_id && candidate.skill_analysis && (
                    <div className="bg-gray-50 mt-4 p-4 rounded-lg">
                      <h4 className="mb-3 font-medium text-gray-900 text-sm">Detailed Skill Analysis</h4>
                      <div className="space-y-3">
                        {Object.entries(candidate.skill_analysis).map(([skill, analysis]) => (
                          <div key={skill} className="bg-white p-3 border rounded">
                            <div className="flex justify-between items-center mb-2">
                              <h5 className="font-medium text-gray-800">{skill}</h5>
                              <span className={`font-bold ${getScoreColor(analysis.score)}`}>
                                {analysis.score}/10
                              </span>
                            </div>
                            {analysis.years_experience && (
                              <p className="mb-2 text-gray-600 text-sm">
                                {analysis.years_experience} years of experience
                              </p>
                            )}
                            {analysis.evidence.length > 0 && (
                              <div>
                                <p className="mb-1 font-medium text-gray-700 text-sm">Evidence:</p>
                                <ul className="text-gray-600 text-sm list-disc list-inside">
                                  {analysis.evidence.map((evidence, evidenceIndex) => (
                                    <li key={evidenceIndex}>{evidence}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {candidate.red_flags && candidate.red_flags.length > 0 && (
                    <div>
                      <h4 className="font-medium text-red-700 text-sm">Red Flags</h4>
                      <ul className="text-red-600 text-sm list-disc list-inside">
                        {candidate.red_flags.map((flag, flagIndex) => (
                          <li key={flagIndex}>{flag}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {/* Candidate Contact Details & Links */}
                  {candidate.candidate_details && (candidate.candidate_details.other_links?.length > 0 || candidate.candidate_details.portfolio) && (
                    <div>
                      <h4 className="font-medium text-gray-700 text-sm">Projects & Links</h4>
                      <div className="space-y-2 mt-2">
                        {candidate.candidate_details.portfolio && (
                          <div className="flex items-center">
                            <span className="bg-green-500 mr-2 rounded-full w-2 h-2"></span>
                            <a
                              href={candidate.candidate_details.portfolio}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-green-600 hover:text-green-800 text-sm hover:underline"
                            >
                              🌐 Main Portfolio
                            </a>
                          </div>
                        )}
                        {candidate.candidate_details.other_links?.map((link, linkIndex) => (
                          <div key={linkIndex} className="flex items-center">
                            <span className="bg-blue-500 mr-2 rounded-full w-2 h-2"></span>
                            <a
                              href={link}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:text-blue-800 text-sm hover:underline"
                            >
                              🔗 {link.includes('demo') ? 'Live Demo' : 
                                   link.includes('project') ? 'Project' :
                                   link.includes('github') ? 'Repository' : 'Website'}
                            </a>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
