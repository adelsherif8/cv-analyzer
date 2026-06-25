'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Plus, Trash2, AlertCircle } from 'lucide-react'
import { JobProfileCreate, SkillWeight } from '../../../lib/schemas'
import { createRole } from '../../../lib/api'

export default function JobForm() {
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const [formData, setFormData] = useState<JobProfileCreate>({
    title: '',
    description: '',
    required_skills: [{ name: '', weight: 0.3 }]
  })

  const addSkill = () => {
    const remainingWeight = 1 - formData.required_skills.reduce((sum, skill) => sum + skill.weight, 0)
    setFormData({
      ...formData,
      required_skills: [...formData.required_skills, { name: '', weight: Math.max(0.1, remainingWeight) }]
    })
  }

  const removeSkill = (index: number) => {
    if (formData.required_skills.length > 1) {
      setFormData({
        ...formData,
        required_skills: formData.required_skills.filter((_, i) => i !== index)
      })
    }
  }

  const updateSkill = (index: number, field: keyof SkillWeight, value: string | number) => {
    const updatedSkills = formData.required_skills.map((skill, i) => 
      i === index ? { ...skill, [field]: value } : skill
    )
    setFormData({ ...formData, required_skills: updatedSkills })
  }

  const getTotalWeight = () => {
    return formData.required_skills.reduce((sum, skill) => sum + skill.weight, 0)
  }

  const getWeightWarning = () => {
    const total = getTotalWeight()
    if (total < 0.9) return 'Total weight is less than 0.9 - consider increasing weights'
    if (total > 1.1) return 'Total weight exceeds 1.1 - consider reducing weights'
    return null
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsLoading(true)

    try {
      // Validate form
      if (!formData.title.trim()) {
        throw new Error('Job title is required')
      }
      if (!formData.description.trim()) {
        throw new Error('Job description is required')
      }
      if (formData.required_skills.some(skill => !skill.name.trim())) {
        throw new Error('All skills must have names')
      }

      const result = await createRole(formData)
      router.push(`/role/${result.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create job profile')
    } finally {
      setIsLoading(false)
    }
  }

  const weightWarning = getWeightWarning()

  return (
    <div className="mx-auto px-4 py-8 max-w-2xl container">
      <div className="bg-white shadow-sm p-6 border rounded-lg">
        <h1 className="mb-6 font-bold text-gray-900 text-2xl">Create Job Profile</h1>
        
        {error && (
          <div className="bg-red-50 mb-6 p-4 border border-red-200 rounded-md">
            <div className="flex">
              <AlertCircle className="w-5 h-5 text-red-400" />
              <div className="ml-3">
                <p className="text-red-700 text-sm">{error}</p>
              </div>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Job Title */}
          <div>
            <label htmlFor="title" className="block mb-2 font-medium text-gray-700 text-sm">
              Job Title
            </label>
            <input
              type="text"
              id="title"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="px-3 py-2 border border-gray-300 focus:border-transparent rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 w-full"
              placeholder="e.g., Senior Shopify Developer"
              required
            />
          </div>

          {/* Job Description */}
          <div>
            <label htmlFor="description" className="block mb-2 font-medium text-gray-700 text-sm">
              Job Description
            </label>
            <textarea
              id="description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={4}
              className="px-3 py-2 border border-gray-300 focus:border-transparent rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 w-full"
              placeholder="Describe the role, responsibilities, and requirements..."
              required
            />
          </div>

          {/* Required Skills */}
          <div>
            <div className="flex justify-between items-center mb-4">
              <label className="block font-medium text-gray-700 text-sm">
                Required Skills & Weights
              </label>
              <span className="text-gray-500 text-sm">
                Total: {getTotalWeight().toFixed(2)}
              </span>
            </div>

            {weightWarning && (
              <div className="bg-yellow-50 mb-4 p-3 border border-yellow-200 rounded-md">
                <p className="text-yellow-700 text-sm">{weightWarning}</p>
              </div>
            )}

            <div className="space-y-3">
              {formData.required_skills.map((skill, index) => (
                <div key={index} className="flex items-center gap-3">
                  <div className="flex-1">
                    <input
                      type="text"
                      value={skill.name}
                      onChange={(e) => updateSkill(index, 'name', e.target.value)}
                      className="px-3 py-2 border border-gray-300 focus:border-transparent rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 w-full"
                      placeholder="e.g., Liquid templating"
                      required
                    />
                  </div>
                  <div className="w-24">
                    <input
                      type="number"
                      value={skill.weight}
                      onChange={(e) => updateSkill(index, 'weight', parseFloat(e.target.value) || 0)}
                      min="0"
                      max="1"
                      step="0.1"
                      className="px-3 py-2 border border-gray-300 focus:border-transparent rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 w-full"
                      required
                    />
                  </div>
                  <button
                    type="button"
                    onClick={() => removeSkill(index)}
                    disabled={formData.required_skills.length === 1}
                    className="p-2 text-red-500 hover:text-red-700 disabled:text-gray-300 disabled:cursor-not-allowed"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>

            <button
              type="button"
              onClick={addSkill}
              className="flex items-center gap-2 mt-3 font-medium text-blue-600 hover:text-blue-700 text-sm"
            >
              <Plus className="w-4 h-4" />
              Add Skill
            </button>
          </div>

          {/* Submit Button */}
          <div className="flex gap-4 pt-6">
            <button
              type="submit"
              disabled={isLoading}
              className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 px-4 py-2 rounded-md font-medium text-white disabled:cursor-not-allowed"
            >
              {isLoading ? 'Creating...' : 'Create Job Profile'}
            </button>
            <button
              type="button"
              onClick={() => router.push('/')}
              className="hover:bg-gray-50 px-6 py-2 border border-gray-300 rounded-md font-medium text-gray-700"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
