# Investment Research AI Platform

A production-grade AI platform for financial research that demonstrates enterprise-level AI engineering skills. This system combines advanced RAG (Retrieval-Augmented Generation), multi-agent orchestration, and comprehensive evaluation to create an intelligent financial document analysis tool.

## 🎯 Core Features

- **Advanced RAG Pipeline**: Hybrid retrieval with vector + keyword search, query transformation, and reranking
- **Multi-Agent System**: Specialized agents orchestrated with LangGraph for complex queries
- **Comprehensive Evaluation**: RAGAS metrics, custom financial metrics, and LLM-as-judge
- **Production-Ready**: Full observability, security, error handling, and deployment configs
- **Beautiful UI**: Modern React interface with real-time streaming and agent trace visualization

## 🏗️ Architecture

- **Frontend**: React 18 + TypeScript + Vite + shadcn/ui + Tailwind
- **Backend**: FastAPI + Python 3.11
- **Database**: Supabase (PostgreSQL + pgvector)
- **LLM Stack**: OpenAI, Anthropic, LangGraph, LiteLLM
- **Deployment**: Modal (serverless) + Vercel

## 📁 Project Structure

```
investment-research-ai/
├── frontend/          # React application
├── backend/           # FastAPI Python application
│   ├── src/
│   │   ├── api/      # API routes and endpoints
│   │   ├── agents/   # Multi-agent system
│   │   ├── rag/      # RAG pipeline
│   │   ├── llm/      # LLM provider abstraction
│   │   ├── evaluation/ # Evaluation framework
│   │   ├── security/ # Auth and input validation
│   │   └── db/       # Database and vector store
│   └── tests/        # Test suite
├── data/             # Golden dataset and sample docs
├── scripts/          # Setup and utility scripts
└── docs/             # Detailed documentation
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Poetry 1.7+ (install: `curl -sSL https://install.python-poetry.org | python3 -`)
- Node.js 18+
- pnpm 8+ (install: `npm install -g pnpm`)
- Supabase account
- OpenAI API key

### Setup

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd investment-research-ai
```

2. **Setup Supabase**
- Create a project at [supabase.com](https://supabase.com)
- Run the schema: `scripts/setup_supabase.sql`
- Get your credentials (URL, anon key, service key)

3. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your credentials
```

4. **Setup Backend**
```bash
cd backend
# Install dependencies with Poetry
poetry install

# Activate Poetry shell
poetry shell

# Or run without activating shell
poetry run uvicorn src.api.main:app --reload
```

5. **Setup Frontend**
```bash
cd frontend
pnpm install
```

6. **Run locally**
```bash
# Terminal 1 - Backend
cd backend
poetry run uvicorn src.api.main:app --reload

# Terminal 2 - Frontend
cd frontend
pnpm dev
```

Visit `http://localhost:3000`

## 📚 Documentation

See `docs/` folder for detailed implementation guides:

- [plan.md](docs/plan.md) - Master plan and architecture
- [agents-implementation.md](docs/agents-implementation.md) - Multi-agent system details
- [rag-implementation.md](docs/rag-implementation.md) - RAG pipeline details
- [evaluation-implementation.md](docs/evaluation-implementation.md) - Evaluation framework
- [deployment-guide.md](docs/deployment-guide.md) - Production deployment

## 🧪 Testing

```bash
# Run all tests
cd backend
poetry run pytest

# Run with coverage
poetry run pytest --cov=src --cov-report=html

# Run evaluations
poetry run python scripts/run_evals.py
```

## 🚢 Deployment

### Backend (Modal)
```bash
cd backend
modal deploy modal_app.py
```

### Frontend (Vercel)
```bash
cd frontend
vercel deploy
```

## 📊 Key Metrics

- **Faithfulness**: >0.85
- **Answer Relevancy**: >0.90
- **Context Precision**: >0.80
- **Numerical Accuracy**: >95%
- **P50 Latency**: <3 seconds

## 🔐 Security

- API key authentication
- Prompt injection defense
- Input validation and sanitization
- Rate limiting
- PII detection (optional)

## 💰 Cost

- Development: ~$15-20
- Monthly (light usage): ~$2-5
- Scales to zero when idle

## 📝 License

MIT

## 🤝 Contributing

This is a portfolio project. Feel free to fork and adapt for your own use!

## 📧 Contact

[Your contact information]

---

**Built with ❤️ to demonstrate production-grade AI engineering skills**
