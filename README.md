# Trading Dashboard MVP

A trading performance analytics platform that helps traders visualize their realized P&L, analyze patterns, and receive AI-powered coaching insights.

## Features

- **CSV Upload**: Support for Webull, Robinhood, and unified CSV formats
- **Accurate P&L Calculation**: FIFO accounting for both long and short positions
- **Visual Analytics**: Continuous, animated red/green P&L chart with benchmark overlays
- **AI Coach**: OpenAI-powered pattern recognition and risk insights
- **Multiple Timeframes**: ALL, YTD, 6M, 3M, 1M, 1W views (EST timezone)

## Tech Stack

**Frontend**
- React + Vite + TypeScript
- Tailwind CSS + Framer Motion
- Plotly.js for charts
- TanStack Query

**Backend**
- FastAPI (Python 3.11+)
- PostgreSQL
- SQLAlchemy + Alembic
- Pandas for calculations
- OpenAI API

**Deployment**
- Railway (Backend + PostgreSQL)
- GitHub Actions CI/CD

## Project Structure

```
/apps
  /frontend          # React application
  /backend           # FastAPI application
/infra               # Infrastructure configs
/tests               # Test suites
/specs               # API contracts & CSV templates
/docs                # Documentation
```

## Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Backend
DATABASE_URL=postgresql://user:pass@localhost:5432/trading_dashboard
OPENAI_API_KEY=your_openai_api_key
APP_ENV=development
TZ=America/New_York

# Frontend
VITE_API_URL=http://localhost:8000
```

### Local Development

**Backend:**
```bash
cd apps/backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd apps/frontend
npm install
npm run dev
```

## Deployment

### Railway Deployment

This project is configured for one-click deployment to Railway:

1. **Fork/Clone** this repository
2. **Connect to Railway:**
   - Visit [railway.app](https://railway.app)
   - Create new project from GitHub repo
   - Railway will detect `railway.toml` configuration
3. **Set Environment Variables:**
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `DATABASE_URL`: Auto-configured by Railway PostgreSQL
   - `TZ`: America/New_York (optional, defaults to EST)
4. **Deploy:**
   - Railway automatically builds and deploys on push to `main`
   - Database migrations run automatically via Alembic
   - Health check available at `/health`

### Manual Deployment

For other platforms, ensure:
- Python 3.11+ runtime
- PostgreSQL 14+ database
- Environment variables configured
- Run `alembic upgrade head` before starting
- Start with `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## Testing

```bash
# Backend tests
cd apps/backend
pytest

# Frontend tests
cd apps/frontend
npm test

# E2E tests
npm run test:e2e
```

## Documentation

- [Assumptions & Limitations](docs/assumptions.md)
- [Broker CSV Templates](specs/broker_templates/)
- [AI Coach JSON Contract](specs/json_contracts/ai_coach.json)

## Scope & Limitations

**MVP Includes:**
- USD equities/ETFs only
- Long and short positions
- Realized P&L (FIFO)
- No fees, dividends, or corporate actions

**Future Features:**
- Options, crypto, FX support
- Broker API integrations
- Advanced analytics (drawdowns, factor analysis)
- User authentication

## License

MIT
