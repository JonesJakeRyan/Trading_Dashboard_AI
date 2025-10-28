# Trading Dashboard - Local Setup Guide

## Prerequisites

- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** - [Download](https://nodejs.org/)
- **PostgreSQL 14+** - [Download](https://www.postgresql.org/download/)
- **Git** - [Download](https://git-scm.com/downloads)

## Quick Start

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd windsurf-project
```

### 2. Backend Setup

```bash
cd apps/backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env and add your values:
# - DATABASE_URL (your local PostgreSQL connection string)
# - OPENAI_API_KEY (your OpenAI API key)
```

### 3. Database Setup

```bash
# Create database (if not exists)
createdb trading_dashboard

# Run migrations
alembic upgrade head
```

### 4. Start Backend

```bash
# From apps/backend directory
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000
- Health check: http://localhost:8000/health
- API docs: http://localhost:8000/docs

### 5. Frontend Setup

Open a new terminal:

```bash
cd apps/frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Start development server
npm run dev
```

Frontend will be available at: http://localhost:3000

## Verification

### Backend Tests

```bash
cd apps/backend
pytest -v
```

Expected output:
```
tests/test_main.py::test_health_check PASSED
tests/test_main.py::test_root_endpoint PASSED
```

### Frontend Tests

```bash
cd apps/frontend
npm test -- --run
```

### Manual Verification

1. **Backend Health Check**
   ```bash
   curl http://localhost:8000/health
   ```
   Should return: `{"status":"healthy","service":"trading-dashboard-api","version":"0.1.0"}`

2. **Frontend Connection**
   - Open http://localhost:3000
   - Should see "Trading Dashboard MVP" heading
   - Backend status should show "healthy" in green

## Common Issues

### Database Connection Error

**Problem:** `sqlalchemy.exc.OperationalError: could not connect to server`

**Solution:**
1. Ensure PostgreSQL is running: `pg_isready`
2. Verify DATABASE_URL in `.env` is correct
3. Check database exists: `psql -l`

### Port Already in Use

**Problem:** `Address already in use`

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000
# Kill the process
kill -9 <PID>
```

### Python Module Not Found

**Problem:** `ModuleNotFoundError`

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate
# Reinstall dependencies
pip install -r requirements.txt
```

### Node Module Errors

**Problem:** `Cannot find module`

**Solution:**
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

## Development Workflow

### Running Tests

```bash
# Backend tests with coverage
cd apps/backend
pytest --cov=app --cov-report=html

# Frontend tests with UI
cd apps/frontend
npm run test:ui

# Lint checks
cd apps/backend
flake8 app/

cd apps/frontend
npm run lint
```

### Database Migrations

```bash
# Create new migration
cd apps/backend
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

### Code Formatting

```bash
# Backend (install black first: pip install black)
black apps/backend/app/

# Frontend
cd apps/frontend
npm run lint --fix
```

## Next Steps

Once Epic A is verified:
- [ ] Backend health check passes
- [ ] Frontend connects to backend
- [ ] All tests pass
- [ ] Ready to proceed to **Epic B: Ingest & Validation**

## Getting Help

- Check [docs/assumptions.md](docs/assumptions.md) for project scope
- Review [LLM_PLAN/Product_Requirement_Document.md](LLM_PLAN/Product_Requirement_Document.md)
- See [infra/railway-setup.md](infra/railway-setup.md) for deployment
