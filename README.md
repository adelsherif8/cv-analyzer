# CV Analyzer

> **Upload a resume + a job description, get an instant AI fit report.** Parses PDF/DOCX resumes, scores them against the role, and returns structured feedback on strengths, gaps, and matched skills — built for recruiters and candidates alike.

![Next.js](https://img.shields.io/badge/Next.js-14-000000?logo=next.js&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?logo=fastapi&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-412991?logo=openai&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)

**▶️ Live demo:** https://cv-analyzer-rust.vercel.app — upload a CV + a job profile and get a ranked, AI-scored fit report (single Next.js app on Vercel, no separate backend).

---

## Features

- 📄 **Resume parsing** — extracts structured data from PDF and DOCX (PyMuPDF + `python-docx`)
- 🎯 **Fit scoring** — scores a candidate against a job profile with an explainable breakdown
- 🔎 **RAG-grounded summaries** — the CV is chunked, embedded, and the passages most relevant to the role are **retrieved** and used to ground the LLM summary (instead of blind truncation). Semantic retrieval via OpenAI embeddings when a key is set; dependency-free TF-IDF fallback otherwise. Retrieved passages are returned in the API response (`retrieved_context`)
- 🧠 **Skill-gap analysis** — surfaces matched skills, missing skills, and improvement feedback via a skill ontology
- 🧪 **Works without a key** — a built-in `mock_ai` mode returns realistic results offline, so the app is fully demoable without an OpenAI key
- 📤 **Exportable results** — structured JSON/report output for downstream use

## Tech Stack

- **Frontend:** Next.js 14 (App Router) + TypeScript + Tailwind CSS
- **Backend:** Python 3.11, FastAPI, OpenAI SDK (hand-built analysis *chains*, no framework lock-in)
- **RAG:** CV chunking + OpenAI `text-embedding-3-small` semantic retrieval (cosine over a NumPy matrix), with a pure-Python TF-IDF fallback — see [`app/services/rag.py`](./CV/backend/app/services/rag.py)
- **Parsing:** PyMuPDF (PDF), `python-docx` (Word)

## Repository Layout

```
CV/
  ├─ backend/                FastAPI service
  │   └─ app/services/       parsing, analysis chains, skill ontology, mock AI
  └─ frontend/               Next.js + Tailwind UI
```

## Quick Start

**Backend:**
```bash
cd CV/backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # add OPENAI_API_KEY (or leave blank for mock mode)
uvicorn app.main:app --reload  # http://localhost:8000
```

**Frontend:**
```bash
cd CV/frontend
npm install
npm run dev                    # http://localhost:3000
```

## Configuration

The backend reads `OPENAI_API_KEY` from `CV/backend/.env`. A `.env.example` template is included; real `.env` files are git-ignored and never committed. With no key set, the app runs in **mock mode** so you can try the full flow instantly.
