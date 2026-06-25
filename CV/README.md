# CV Analyzer MVP

A complete MVP for HR teams to analyze CVs against job profiles using AI.

## Tech Stack

- **Frontend**: Next.js 14 (App Router) + TypeScript + TailwindCSS
- **Backend**: Python 3.11, FastAPI, LangChain, OpenAI
- **File Processing**: PyMuPDF, python-docx, pdfminer.six
- **Storage**: Local disk (MVP), CSV/PDF exports

## Prerequisites

- Python 3.11+
- Node.js 18+
- OpenAI API key

## Setup

1. Copy environment files:
```bash
cp .env.example .env
cp backend/.env.example backend/.env
```

2. Set your OpenAI API key in both `.env` files:
```
OPENAI_API_KEY=your_openai_api_key_here
```

## Development

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Usage

1. Go to http://localhost:3000
2. Click "Create Job Profile"
3. Fill in job details and required skills with weights
4. Upload 3-10 CVs (PDF/DOC/DOCX)
5. Click "Analyze" to run AI analysis
6. View results in sortable table
7. Click candidates for detailed analysis
8. Export results as CSV or PDF

## Features

- **Job Profile Creation**: Define roles with weighted skill requirements
- **Multi-file CV Upload**: Support for PDF, DOC, DOCX formats
- **AI Analysis**: LangChain + OpenAI for intelligent CV evaluation
- **Scoring System**: Hybrid scoring with skill matching and experience
- **Results Dashboard**: Sortable table with candidate drawer
- **Export Options**: CSV and PDF export functionality
- **Privacy Controls**: Delete all data functionality

## Configuration

### Model Settings
Edit `MODEL_NAME` in `.env` to switch AI models:
- `gpt-4o-mini` (default, cost-effective)
- `gpt-4o` (higher quality, more expensive)

### Data Storage
Files stored in:
- Uploads: `backend/app/data/uploads/{role_id}/`
- Results: `backend/app/data/results/{role_id}.json`
- Roles: `backend/app/data/roles/{role_id}.json`

## TODOs for Production

- [ ] Replace local storage with S3/cloud storage
- [ ] Add user authentication and multi-tenancy
- [ ] Implement PostgreSQL for metadata storage
- [ ] Add Celery + Redis for background processing
- [ ] Set up monitoring with Prometheus + Grafana
- [ ] Add comprehensive error handling and logging
- [ ] Implement rate limiting and API quotas
- [ ] Add audit trails and compliance features

## Quality Assurance

The MVP meets these acceptance criteria:
- ✅ Create role → upload ≥5 CVs → analyze → get valid results
- ✅ Scores show one decimal place, table sorts correctly
- ✅ Candidate drawer shows all fields including optional red flags
- ✅ CSV and PDF export functionality works
- ✅ Delete role removes all associated data
- ✅ Handles common file format issues gracefully

## Privacy & Security

- Files encrypted at rest locally in this MVP
- Data can be deleted anytime via "Delete all data" button
- Auto-purge in 30 days (configurable)
- We do not train models on your data
- No PII used in AI model features
