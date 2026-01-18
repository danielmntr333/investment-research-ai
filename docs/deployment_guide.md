# Deployment Guide - Step-by-Step Production Deployment

## Overview

This guide walks you through deploying the complete Investment Research AI platform to production using Modal (backend) and Vercel (frontend).

**Stack**:
- Backend: Modal (serverless Python)
- Frontend: Vercel (React)
- Database: Supabase (Postgres + pgvector + Storage)
- Monitoring: LangSmith

**Total Setup Time**: ~30-45 minutes

---

## Prerequisites

### Required Accounts (All Free Tier Available)
- [ ] GitHub account (for code hosting)
- [ ] Supabase account (database)
- [ ] Modal account (backend hosting)
- [ ] Vercel account (frontend hosting)
- [ ] OpenAI account (LLM API)
- [ ] Anthropic account (Claude API)
- [ ] Cohere account (reranking)
- [ ] LangSmith account (observability)

### Required Tools
```bash
# Install Python 3.11+
python --version  # Should be 3.11 or higher

# Install Node.js 18+
node --version  # Should be 18 or higher

# Install Git
git --version
```

---

## Phase 1: Supabase Setup (Database & Storage)

### Step 1.1: Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Click "Start your project"
3. Create new organization (if needed)
4. Click "New project"
   - Name: `investment-research-ai`
   - Database password: Generate strong password (SAVE THIS!)
   - Region: Choose closest to you
   - Plan: Free tier
5. Wait for project to provision (~2 minutes)

### Step 1.2: Enable pgvector Extension

1. In Supabase dashboard, go to "SQL Editor"
2. Click "New query"
3. Paste and run:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Step 1.3: Run Database Migration

1. Copy the schema from `scripts/setup_supabase.sql`
2. In SQL Editor, paste the complete schema
3. Click "Run"
4. Verify tables created: Go to "Table Editor" and see all tables

### Step 1.4: Get Credentials

1. Go to Project Settings → API
2. Save these values:
   - **Project URL**: `https://xxx.supabase.co`
   - **anon public key**: `eyJhbG...`
   - **service_role key**: `eyJhbG...` (keep secret!)

### Step 1.5: Setup Storage Buckets

1. Go to "Storage" in dashboard
2. Create new bucket:
   - Name: `documents`
   - Public: No
   - File size limit: 10MB
3. Set RLS policies:

```sql
-- Allow authenticated users to upload
CREATE POLICY "Users can upload documents"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'documents');

-- Allow users to read their own documents
CREATE POLICY "Users can read own documents"
ON storage.objects FOR SELECT
TO authenticated
USING (bucket_id = 'documents');
```

---

## Phase 2: API Keys Setup

### Step 2.1: OpenAI API Key

1. Go to [platform.openai.com](https://platform.openai.com)
2. Navigate to API keys
3. Click "Create new secret key"
4. Name it: `investment-research-ai`
5. Copy key (starts with `sk-`): `sk-...`
6. Add billing method (prepaid $5-10 recommended)

### Step 2.2: Anthropic API Key

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Navigate to API keys
3. Create new key
4. Copy key (starts with `sk-ant-`): `sk-ant-...`
5. Add credits ($5 recommended)

### Step 2.3: Cohere API Key

1. Go to [cohere.com](https://cohere.com)
2. Sign up for free account
3. Go to API keys
4. Copy Production key
5. Free tier: 100 rerank calls/month

### Step 2.4: LangSmith API Key

1. Go to [smith.langchain.com](https://smith.langchain.com)
2. Create account
3. Create new project: `investment-research-ai`
4. Go to Settings → API keys
5. Create key, copy it
6. Free tier: 5,000 traces/month

### Step 2.5: Tavily API Key (Optional - Web Search)

1. Go to [tavily.com](https://tavily.com)
2. Sign up
3. Get API key
4. Free tier: 1,000 searches/month

---

## Phase 3: Backend Deployment (Modal)

### Step 3.1: Install Poetry and Modal

```bash
# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Or on Windows PowerShell:
# (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

# Install Modal globally or use poetry
pip install modal
# Or: poetry add --group dev modal
```

### Step 3.2: Setup Modal Account

```bash
# Login to Modal
modal setup

# This will open browser to authenticate
# Choose "Hobby" plan (free tier)
```

### Step 3.3: Create Modal Secrets

```bash
# OpenAI secret
modal secret create openai-secret \
  OPENAI_API_KEY=sk-...

# Anthropic secret
modal secret create anthropic-secret \
  ANTHROPIC_API_KEY=sk-ant-...

# Supabase secret
modal secret create supabase-secret \
  SUPABASE_URL=https://xxx.supabase.co \
  SUPABASE_ANON_KEY=eyJhbG... \
  SUPABASE_SERVICE_KEY=eyJhbG...

# Cohere secret
modal secret create cohere-secret \
  COHERE_API_KEY=...

# LangSmith secret
modal secret create langsmith-secret \
  LANGSMITH_API_KEY=... \
  LANGSMITH_PROJECT=investment-research-ai

# Tavily secret (optional)
modal secret create tavily-secret \
  TAVILY_API_KEY=...
```

### Step 3.4: Deploy to Modal

```bash
cd backend

# Deploy
modal deploy modal_app.py

# You'll see output like:
# ✓ Created app investment-research-ai
# ✓ Deployed function fastapi_app
# View at https://your-app-url.modal.run
```

### Step 3.5: Test Backend

```bash
# Test health endpoint
curl https://your-app-url.modal.run/health

# Should return: {"status": "healthy"}
```

### Step 3.6: Get Backend URL

Save your Modal URL: `https://your-app-url.modal.run`

You'll need this for the frontend!

---

## Phase 4: Frontend Deployment (Vercel)

### Step 4.1: Push Code to GitHub

```bash
# Initialize git repo (if not already)
cd ..  # Back to project root
git init

# Add files
git add .

# Commit
git commit -m "Initial commit"

# Create GitHub repo (via GitHub website)
# Then:
git remote add origin https://github.com/your-username/investment-research-ai.git
git branch -M main
git push -u origin main
```

### Step 4.2: Deploy to Vercel

1. Go to [vercel.com](https://vercel.com)
2. Sign in with GitHub
3. Click "New Project"
4. Import your repository
5. Configure project:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `pnpm build`
   - **Output Directory**: `dist`

6. Add Environment Variables:
   ```
   VITE_API_URL=https://your-app-url.modal.run
   ```

7. Click "Deploy"
8. Wait ~2 minutes
9. Your app is live! `https://your-app.vercel.app`

### Step 4.3: Configure Custom Domain (Optional)

1. In Vercel project settings → Domains
2. Add your domain: `research.yourdomain.com`
3. Follow DNS instructions
4. Wait for SSL certificate (automatic)

---

## Phase 5: Post-Deployment Setup

### Step 5.1: Initial Setup

> **Note**: Authentication is not currently implemented (personal use app).  
> OAuth 2.0 will be added in a future enhancement.

**For now, the app is open for personal use without authentication.**

### Step 5.2: Upload Sample Documents

1. Go to your deployed frontend: `https://your-app.vercel.app`
2. Upload a sample PDF (try a financial report)
3. Wait for processing (~30 seconds)
4. Test a query: "What is this document about?"

**Future Enhancement**: When OAuth is implemented, users will:
- Sign in with Google/GitHub
- Have personal document libraries
- Track their own usage quotas

### Step 5.3: Verify Everything Works

**Test Checklist**:
- [ ] Document upload works
- [ ] Document processing completes
- [ ] Chat query returns answer
- [ ] Sources are shown
- [ ] Citations are present
- [ ] Agent trace is visible
- [ ] Metrics dashboard loads

---

## Phase 6: Monitoring & Observability

### Step 6.1: Verify LangSmith Integration

1. Go to [smith.langchain.com](https://smith.langchain.com)
2. Click on your project
3. Send a query from your app
4. Refresh LangSmith - you should see the trace!

### Step 6.2: Setup Modal Monitoring

```bash
# View logs
modal app logs investment-research-ai

# View metrics
modal app list

# Monitor costs
modal account usage
```

### Step 6.3: Setup Supabase Monitoring

1. In Supabase dashboard → Reports
2. Monitor:
   - Database size
   - API requests
   - Storage usage
3. Set up alerts (Settings → Alerts):
   - Database > 400MB (near free limit)
   - High error rate

---

## Phase 7: Configure CI/CD (GitHub Actions)

### Step 7.1: Create GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install Poetry
        run: |
          curl -sSL https://install.python-poetry.org | python3 -
          echo "$HOME/.local/bin" >> $GITHUB_PATH
      
      - name: Install dependencies
        run: |
          cd backend
          poetry install
      
      - name: Lint
        run: |
          cd backend
          poetry run ruff check src/
      
      - name: Type check
        run: |
          cd backend
          poetry run mypy src/
      
      - name: Test
        run: |
          cd backend
          poetry run pytest tests/ -v

  deploy-backend:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install Modal
        run: |
          curl -sSL https://install.python-poetry.org | python3 -
          echo "$HOME/.local/bin" >> $GITHUB_PATH
          pip install modal
      
      - name: Deploy to Modal
        env:
          MODAL_TOKEN_ID: ${{ secrets.MODAL_TOKEN_ID }}
          MODAL_TOKEN_SECRET: ${{ secrets.MODAL_TOKEN_SECRET }}
        run: |
          cd backend
          modal deploy modal_app.py
```

### Step 7.2: Add GitHub Secrets

1. Get Modal token:
```bash
modal token show
# Copy the token_id and token_secret
```

2. In GitHub repo → Settings → Secrets and variables → Actions
3. Add secrets:
   - `MODAL_TOKEN_ID`
   - `MODAL_TOKEN_SECRET`

Now every push to `main` will automatically test and deploy!

---

## Phase 8: Load Sample Data

### Step 8.1: Create Golden Dataset

```bash
cd data/golden_dataset

# Create questions.json
cat > questions.json << 'EOF'
[
  {
    "id": "test_001",
    "question": "What is the revenue?",
    "expected_answer": "Sample answer",
    "difficulty": "easy",
    "required_capabilities": ["factual_retrieval"]
  }
]
EOF
```

### Step 8.2: Run Initial Evaluation

```python
# Run locally to establish baseline
python scripts/run_evals.py
```

This creates baseline metrics for regression testing.

---

## Phase 9: Cost Optimization

### Configure Modal Auto-scaling

In `modal_app.py`:

```python
@stub.function(
    keep_warm=1,  # Keep 1 container warm
    container_idle_timeout=300,  # 5 minutes
    timeout=300,  # 5 minute max execution
)
```

### Setup Embedding Cache

Already configured in code - verify it's working:
- Check cache hit rate in logs
- Should be >60% after initial queries

### Monitor Costs

```bash
# Check Modal costs
modal account usage

# Check OpenAI costs
# Go to platform.openai.com/usage

# Check Anthropic costs
# Go to console.anthropic.com/settings/billing
```

**Expected costs**:
- Development: $5-15/month
- Light production: $10-30/month
- When idle: $0/month (Modal scales to zero!)

---

## Phase 10: Security Hardening

### Step 10.1: Setup CORS Properly

In `backend/src/api/main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-app.vercel.app",
        "http://localhost:3000"  # For local dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Step 10.2: Setup Rate Limiting

Already in code - verify it works:

```bash
# Test rate limiting
for i in {1..30}; do
  curl -H "X-API-Key: YOUR_KEY" https://your-app.modal.run/api/chat
done

# Should get 429 error after ~20 requests
```

### Step 10.3: Enable Supabase RLS

Run these policies:

```sql
-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- Users can only see their own data
CREATE POLICY "Users can read own documents"
ON documents FOR SELECT
USING (user_id = auth.uid());

-- Add similar policies for other tables
```

---

## Troubleshooting

### Issue: Modal deployment fails

**Solution**:
```bash
# Check Modal status
modal app list

# View detailed logs
modal app logs investment-research-ai --live

# Redeploy
modal deploy modal_app.py --force
```

### Issue: Supabase connection timeout

**Solution**:
```python
# Check connection
from supabase import create_client
client = create_client(URL, KEY)
result = client.table('users').select("*").limit(1).execute()
print(result)
```

### Issue: Frontend can't reach backend

**Solution**:
1. Check CORS configuration
2. Verify VITE_API_URL in Vercel
3. Test backend directly:
```bash
curl https://your-app.modal.run/health
```

### Issue: pgvector queries slow

**Solution**:
```sql
-- Rebuild index
DROP INDEX IF EXISTS idx_chunks_embedding;
CREATE INDEX idx_chunks_embedding ON document_chunks 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- Analyze table
ANALYZE document_chunks;
```

### Issue: High LLM costs

**Solution**:
1. Check embedding cache hit rate
2. Reduce top_k in retrieval (10 → 5)
3. Use smaller models for dev/test
4. Enable aggressive caching

---

## Maintenance

### Daily
- [ ] Check Modal logs for errors
- [ ] Monitor API costs (OpenAI, Anthropic)
- [ ] Verify evaluation metrics stable

### Weekly
- [ ] Review Supabase storage usage
- [ ] Check LangSmith traces for issues
- [ ] Review user feedback (if any)

### Monthly
- [ ] Run full evaluation suite
- [ ] Update dependencies
- [ ] Review and optimize costs
- [ ] Backup database

---

## Rollback Procedure

If something breaks in production:

```bash
# Rollback backend
modal app versions investment-research-ai
modal app rollback investment-research-ai <previous-version>

# Rollback frontend (in Vercel dashboard)
# Deployments → Previous deployment → "Promote to Production"

# Rollback database (if needed)
# In Supabase: Database → Backups → Restore
```

---

## Success Checklist

✅ **Infrastructure**:
- [ ] Supabase project created and configured
- [ ] pgvector extension enabled
- [ ] All tables created
- [ ] Storage buckets setup

✅ **Backend**:
- [ ] Modal app deployed
- [ ] All secrets configured
- [ ] Health endpoint responding
- [ ] Can upload documents
- [ ] Can query documents

✅ **Frontend**:
- [ ] Vercel deployment successful
- [ ] Environment variables set
- [ ] Can connect to backend
- [ ] UI loads properly

✅ **Monitoring**:
- [ ] LangSmith receiving traces
- [ ] Modal logs visible
- [ ] Supabase metrics tracking

✅ **Testing**:
- [ ] End-to-end test passed
- [ ] Evaluation metrics calculated
- [ ] No errors in logs

---

## URLs to Save

```
Supabase Dashboard: https://app.supabase.com/project/YOUR_PROJECT
Modal Dashboard: https://modal.com/apps
Vercel Dashboard: https://vercel.com/YOUR_USERNAME
LangSmith Dashboard: https://smith.langchain.com/

Production URLs:
Backend API: https://your-app.modal.run
Frontend: https://your-app.vercel.app

Service API Keys: (Store in password manager!)
- Supabase service_role key
- OpenAI API key
- Anthropic API key
- Cohere API key
- LangSmith API key

Note: User authentication not implemented (personal use app)
```

---

## Next Steps

1. **Add OAuth Authentication**: Implement OAuth 2.0 (Google, GitHub) for multi-user support
2. **Custom Domain**: Setup custom domain for professional look
3. **Analytics**: Add usage analytics (PostHog, Mixpanel)
4. **User Feedback**: Implement feedback collection
5. **Scaling**: Monitor and optimize as usage grows

**Future Authentication Plan**:
- OAuth 2.0 with Google/GitHub providers
- User-specific document storage
- Per-user usage tracking and quotas
- Session management with httpOnly cookies

**You're now live in production! 🚀**