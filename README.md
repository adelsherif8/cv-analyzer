# CV Analyzer

An AI-powered CV/resume analyzer for HR teams — upload a CV and score it against
a job profile, with structured feedback on strengths, gaps, and fit. Parses PDF
and DOCX resumes and reasons over them with an LLM.

## Tech Stack

- **Frontend:** Next.js 14 (App Router) + TypeScript + Tailwind CSS
- **Backend:** Python 3.11, FastAPI, LangChain, OpenAI
- **Parsing:** PyMuPDF (PDF), `python-docx` (Word)

## Repository Layout

```
CV/          Main application
  ├─ backend/   FastAPI service (parsing + AI analysis)
  └─ ...        Next.js frontend + docs
CV NEW/      Iteration / work-in-progress version
```

See `CV/README.md` and `CV/SETUP_GUIDE.md` for full setup details.

## Quick Start (backend)

```bash
cd CV/backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # add your OPENAI_API_KEY
uvicorn app.main:app --reload
```

## Configuration

The backend reads `OPENAI_API_KEY` from a `.env` file. A `.env.example` template
is included; real `.env` files are git-ignored and never committed.
