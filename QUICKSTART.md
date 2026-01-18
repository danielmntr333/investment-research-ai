# Quick Start Guide

Get the Investment Research AI app running in 5 minutes!

## Prerequisites

- Python 3.11+
- Node.js 18+
- pnpm (install with: `npm install -g pnpm`)
- Poetry (install from: https://python-poetry.org/docs/#installation)
- Supabase account (free tier works!)
- OpenAI API key

## Step 1: Clone and Setup Environment

```bash
# Copy environment template
cp .env.example backend/.env

# Edit backend/.env and add your keys:
# - SUPABASE_URL
# - SUPABASE_SERVICE_KEY
# - OPENAI_API_KEY
```

## Step 2: Database Setup

1. Go to your Supabase project dashboard
2. Open SQL Editor
3. Run this SQL:

```sql
-- Run the database schema
-- File: scripts/setup_supabase.sql
-- (Or use the manual schema from docs/plan.md)

-- Essential: Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Then run the FTS migration
-- File: backend/migrations/add_fts_support.sql
```

## Step 3: Install Dependencies

**Backend:**
```bash
cd backend
poetry install
```

**Frontend:**
```bash
cd frontend
pnpm install
```

## Step 4: Run the Application

Open **two terminals**:

**Terminal 1 - Backend:**
```bash
cd backend
poetry run uvicorn src.api.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
pnpm dev
```

## Step 5: Test It Out

1. Open browser to: http://localhost:5173
2. Go to "Documents" tab
3. Upload a PDF file (try a financial report, 10-K, etc.)
4. Wait for processing (5-15 seconds)
5. Go to "Chat" tab
6. Ask a question about your document!

Example questions:
- "What is this document about?"
- "What are the key financial metrics?"
- "Summarize the main points"

## Step 6: Check Metrics

1. Go to "Metrics" tab
2. View evaluation dashboard
3. See RAG performance metrics

## Troubleshooting

### Backend won't start

**Error: "Supabase credentials not configured"**
- Check `backend/.env` exists and has correct keys
- Verify keys are valid by logging into Supabase

**Error: "OpenAI API key not found"**
- Add `OPENAI_API_KEY=sk-...` to `backend/.env`

**Error: "No module named 'src'"**
- Make sure you're in `backend/` directory
- Run `poetry install`
- Use `poetry run` prefix for all commands

### Frontend won't connect

**Error: "Network request failed"**
- Check backend is running on port 8000
- Visit http://localhost:8000/health
- Should see: `{"status": "healthy"}`

**CORS errors in browser console**
- Backend already has CORS configured
- Make sure ports are correct (frontend: 5173, backend: 8000)

### Document upload fails

**Processing never completes**
- Check backend terminal for errors
- Verify OpenAI API key is valid
- Check if `document_chunks` table exists

**"Document has no content"**
- Try a different PDF
- Some PDFs are image-based (need OCR)
- Make sure PDF has selectable text

### Chat not working

**No response**
- Check backend terminal for errors
- Verify documents are processed (green checkmark)
- Try uploading a document first

**Stream errors**
- Normal for now - backend returns full response
- Check browser network tab for response

## Verify Setup

Run these commands to verify everything is working:

**Test backend:**
```bash
# Should return: {"status": "healthy", "version": "1.0.0"}
curl http://localhost:8000/health

# Should return empty list initially
curl http://localhost:8000/api/documents

# Should return sample metrics
curl http://localhost:8000/api/evals/metrics
```

**Test frontend:**
- Open http://localhost:5173
- Should see the app with sidebar
- No console errors

## What's Next?

Once everything is working:

1. **Upload real documents**: Try financial reports, 10-Ks, earnings calls
2. **Test chat**: Ask complex questions
3. **Compare documents**: Upload multiple docs and ask comparative questions
4. **Check metrics**: See how well the system performs
5. **Customize**: Adjust chunking, models, prompts

## Configuration Options

### Backend Settings (backend/.env)

```bash
# Use GPT-4o for better quality (more expensive)
# Default is gpt-4o-mini
# Modify in: backend/src/llm/provider.py

# Enable reranking for better retrieval
COHERE_API_KEY=your-key

# Enable tracing for debugging
LANGSMITH_API_KEY=your-key
LANGSMITH_PROJECT=investment-research-ai
```

### Frontend Settings

Edit `frontend/src/lib/api.ts`:

```typescript
// Change API base URL if deploying
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
```

## Production Deployment

See `docs/deployment_guide.md` for deploying to:
- Backend: Modal (serverless)
- Frontend: Vercel (free tier)
- Database: Supabase (already set up!)

## Need Help?

Check these files:
- `BACKEND_FRONTEND_INTEGRATION.md` - Full integration guide
- `backend/README_ADVANCED_RAG.md` - RAG pipeline details
- `docs/plan.md` - Complete architecture

## Success!

If you can:
- ✅ Upload a document
- ✅ See it process successfully
- ✅ Ask questions and get answers
- ✅ View metrics

You're all set! The system is working correctly.

---

**Estimated setup time: 5-10 minutes**

**First query time: ~15 seconds** (document upload + processing + first response)

**Subsequent queries: ~2-4 seconds**
