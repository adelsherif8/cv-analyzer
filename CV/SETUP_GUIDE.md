# CV Analyzer MVP - Setup & Usage Guide

## 🚀 Quick Start

The CV Analyzer MVP is now fully operational! Both frontend and backend servers are running:

- **Frontend**: http://localhost:3000 - React/Next.js interface
- **Backend API**: http://localhost:8000 - FastAPI with OpenAI integration
- **API Docs**: http://localhost:8000/docs - Interactive Swagger documentation

## ✅ Current Status

✅ **Backend Server** - Running on port 8000
✅ **Frontend Server** - Running on port 3000  
✅ **Dependencies Installed** - All Python and Node.js packages
✅ **API Integration** - OpenAI GPT-4o-mini for CV analysis
✅ **File Processing** - PDF, DOC, DOCX upload support
✅ **Export Features** - CSV and PDF export capabilities

## 🛠️ Setup Instructions

### Prerequisites Met
- ✅ Python 3.12 with virtual environment
- ✅ Node.js with npm
- ✅ All dependencies installed

### Environment Configuration
1. **OpenAI API Key**: Add your key to `backend/.env`:
   ```
   OPENAI_API_KEY=your-openai-api-key-here
   ```

2. **Optional Redis** (for background tasks):
   ```
   REDIS_URL=redis://localhost:6379/0
   ```

## 🎯 Key Features

### 1. Job Profile Creation
- Create detailed job profiles with weighted skill requirements
- Support for Junior/Mid/Senior/Lead/Executive levels
- Flexible skill weighting system (0.0-1.0)

### 2. CV Analysis Pipeline
- Upload PDF, DOC, or DOCX files
- AI-powered text extraction and analysis
- Skill matching with evidence extraction
- Experience level assessment
- Red flag detection

### 3. Scoring & Results
- Overall fit score (0-10 scale)
- Detailed reasoning with bullet points
- Executive summary generation
- Role suggestions based on candidate profile

### 4. Export Capabilities
- CSV export for spreadsheet analysis
- PDF report generation
- Batch processing support

## 📁 Project Structure

```
CV/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── main.py         # FastAPI app entry point
│   │   ├── config.py       # Settings and configuration
│   │   ├── schemas.py      # Pydantic models
│   │   ├── routers/        # API endpoints
│   │   │   ├── roles.py    # Job profile management
│   │   │   ├── files.py    # File upload handling
│   │   │   └── analyze.py  # CV analysis endpoints
│   │   ├── services/       # Business logic
│   │   │   ├── chains.py   # OpenAI integration
│   │   │   ├── parsing.py  # Document processing
│   │   │   ├── scoring.py  # Scoring algorithms
│   │   │   └── exports.py  # Export functionality
│   │   ├── prompts/        # AI prompt templates
│   │   └── data/           # Sample data and uploads
│   ├── requirements.txt    # Python dependencies
│   ├── .env               # Environment variables
│   └── venv/              # Virtual environment
│
├── frontend/               # Next.js application
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx    # Landing page
│   │   │   ├── layout.tsx  # App layout
│   │   │   └── role/
│   │   │       └── new/
│   │   │           └── page.tsx  # Job creation form
│   │   └── lib/
│   │       ├── api.ts      # API client
│   │       ├── schemas.ts  # Type definitions
│   │       └── utils.ts    # Utilities
│   ├── package.json       # Node.js dependencies
│   └── node_modules/      # Node.js packages
│
├── docker-compose.yml     # Container orchestration
├── README.md             # Project documentation
└── .env.example          # Environment template
```

## 🔧 Development Commands

### Backend Management
```bash
# Navigate to backend
cd backend

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Management
```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## 🧪 Testing the Application

### 1. Test Backend Health
Visit: http://localhost:8000/health
Expected: `{"status": "healthy", "timestamp": "...", "model_name": "gpt-4o-mini"}`

### 2. Test API Documentation
Visit: http://localhost:8000/docs
Expected: Interactive Swagger UI with all endpoints

### 3. Test Frontend
Visit: http://localhost:3000
Expected: CV Analyzer landing page with navigation

### 4. Test Job Creation
1. Go to http://localhost:3000/role/new
2. Fill out job profile form
3. Add required skills with weights
4. Submit to create job profile

### 5. Test CV Analysis
1. Create a job profile first
2. Upload a CV file (PDF/DOC/DOCX)
3. View analysis results with scoring
4. Export results as CSV or PDF

## 📊 Sample Workflow

1. **Create Job Profile**
   - Title: "Senior Frontend Developer"
   - Required Skills: React (0.9), TypeScript (0.8), CSS (0.7)
   - Experience: 5+ years

2. **Upload CV**
   - Select job profile
   - Upload candidate's resume
   - Wait for AI analysis

3. **Review Results**
   - Overall fit score
   - Skill-by-skill breakdown
   - Experience assessment
   - Suggested improvements

4. **Export Data**
   - Generate CSV for HR tracking
   - Create PDF report for managers
   - Batch process multiple candidates

## 🔍 API Endpoints

### Job Management
- `POST /roles` - Create job profile
- `GET /roles` - List all profiles
- `DELETE /roles/{role_id}` - Remove profile

### File Processing
- `POST /files/upload` - Upload CV files
- `GET /files` - List uploaded files

### Analysis
- `POST /analyze/{role_id}` - Analyze CVs against job
- `GET /analyze/{role_id}/export` - Export results

### System
- `GET /health` - Health check
- `GET /docs` - API documentation

## 🚀 Production Deployment

### Environment Variables
```bash
# Required
OPENAI_API_KEY=your-api-key
DEBUG=false
DATA_DIR=/app/data

# Optional
REDIS_URL=redis://redis:6379/0
MAX_CONTENT_LENGTH=16777216
```

### Docker Deployment
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🎯 Next Steps & TODOs

### High Priority
- [ ] Add user authentication and authorization
- [ ] Implement role-based access control
- [ ] Add bulk CV upload processing
- [ ] Create dashboard with analytics

### Medium Priority
- [ ] Add more file format support (TXT, RTF)
- [ ] Implement advanced search and filtering
- [ ] Add candidate database management
- [ ] Create email notification system

### Low Priority
- [ ] Add integration with ATS systems
- [ ] Implement advanced reporting
- [ ] Add API rate limiting
- [ ] Create mobile-responsive design

## 💡 Technical Notes

### AI Model Configuration
- Default model: `gpt-4o-mini`
- Configurable per job profile
- Fallback prompts for offline development
- Token limit management (3000 chars max)

### File Processing
- Supported formats: PDF, DOC, DOCX
- Text extraction using PyMuPDF, python-docx, pdfminer.six
- Error handling for corrupted files
- File size limits configured

### Data Storage
- Local filesystem for MVP
- JSON-based profile storage
- File uploads in `backend/data/uploads/`
- Ready for database migration

## 🆘 Troubleshooting

### Backend Issues
- **Import errors**: Ensure virtual environment is activated
- **OpenAI errors**: Check API key configuration
- **Port conflicts**: Change port in uvicorn command

### Frontend Issues
- **Build errors**: Run `npm install` to install dependencies
- **API connection**: Verify backend is running on port 8000
- **TypeScript errors**: Check type definitions in `lib/schemas.ts`

### Common Solutions
- Restart both servers if experiencing connection issues
- Check environment variables in `.env` files
- Verify all dependencies are installed correctly

---

**🎉 Congratulations! Your CV Analyzer MVP is ready for testing and development.**

For questions or issues, check the logs in your terminal windows or visit the API documentation at http://localhost:8000/docs.
