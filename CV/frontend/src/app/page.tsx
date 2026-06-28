import Link from 'next/link'
import { FileText, Zap, Shield, BarChart3 } from 'lucide-react'

export default function HomePage() {
  return (
    <div className="mx-auto px-4 py-12 container">
      {/* Hero Section */}
      <div className="mb-16 text-center">
        <h1 className="mb-4 font-bold text-gray-900 text-4xl">
          Cut CV screening time by 50% for Shopify/front-end roles
        </h1>
        <p className="mx-auto mb-8 max-w-2xl text-gray-600 text-xl">
          AI-powered CV analysis that ranks candidates, explains fit with evidence, and exports results. 
          Built for HR teams who need fast, reliable candidate evaluation.
        </p>
        
        <div className="flex justify-center gap-4">
          <Link 
            href="/role/new"
            className="bg-blue-600 hover:bg-blue-700 px-8 py-3 rounded-lg font-semibold text-white transition-colors"
          >
            Create Job Profile
          </Link>
          <button className="hover:bg-gray-50 px-8 py-3 border border-gray-300 rounded-lg font-semibold text-gray-700 transition-colors">
            Watch 60s Demo
          </button>
        </div>
      </div>

      {/* Features */}
      <div className="gap-8 grid md:grid-cols-2 lg:grid-cols-4 mb-16">
        <div className="text-center">
          <div className="flex justify-center items-center bg-blue-100 mx-auto mb-4 rounded-lg w-12 h-12">
            <FileText className="w-6 h-6 text-blue-600" />
          </div>
          <h3 className="mb-2 font-semibold text-gray-900">Multi-Format Upload</h3>
          <p className="text-gray-600 text-sm">
            PDF, DOC, DOCX support with OCR for scanned documents
          </p>
        </div>

        <div className="text-center">
          <div className="flex justify-center items-center bg-green-100 mx-auto mb-4 rounded-lg w-12 h-12">
            <Zap className="w-6 h-6 text-green-600" />
          </div>
          <h3 className="mb-2 font-semibold text-gray-900">AI-Powered Analysis</h3>
          <p className="text-gray-600 text-sm">
            LangChain + OpenAI for intelligent skill matching and fit scoring
          </p>
        </div>

        <div className="text-center">
          <div className="flex justify-center items-center bg-purple-100 mx-auto mb-4 rounded-lg w-12 h-12">
            <BarChart3 className="w-6 h-6 text-purple-600" />
          </div>
          <h3 className="mb-2 font-semibold text-gray-900">Evidence-Based Ranking</h3>
          <p className="text-gray-600 text-sm">
            Sortable results with per-skill evidence and gap analysis
          </p>
        </div>

        <div className="text-center">
          <div className="flex justify-center items-center bg-orange-100 mx-auto mb-4 rounded-lg w-12 h-12">
            <Shield className="w-6 h-6 text-orange-600" />
          </div>
          <h3 className="mb-2 font-semibold text-gray-900">Privacy First</h3>
          <p className="text-gray-600 text-sm">
            Local storage, instant deletion, no model training on your data
          </p>
        </div>
      </div>

      {/* Demo Video */}
      <div className="mb-16 text-center">
        <h3 className="mb-1 font-semibold text-gray-900 text-xl">See it in action</h3>
        <p className="mb-5 text-gray-600">
          Create a job profile, upload CVs, and get AI-powered ranked results — in under a minute.
        </p>
        <div className="mx-auto max-w-3xl rounded-xl overflow-hidden shadow-lg ring-1 ring-gray-200">
          <video
            className="w-full"
            src="/demo.mp4"
            controls
            playsInline
            preload="metadata"
            poster="/demo-poster.png"
          />
        </div>
      </div>

      {/* Privacy Note */}
      <div className="bg-blue-50 p-6 border border-blue-200 rounded-lg text-center">
        <h3 className="mb-2 font-semibold text-blue-900">Privacy & Data Protection</h3>
        <p className="text-blue-700 text-sm">
          Files stored encrypted at rest locally in this MVP; delete anytime. 
          Auto-purge in 30 days (configurable). We do not train models on your data.
        </p>
      </div>
    </div>
  )
}
