# 📊 Jones Trading Dashboard

A professional trading performance analytics platform with AI-powered insights, built with FastAPI and React.

![Dashboard Preview](https://img.shields.io/badge/Status-MVP-success)
![Python](https://img.shields.io/badge/Python-3.10+-blue)
![React](https://img.shields.io/badge/React-18+-61dafb)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688)

## 🚀 Features

### Core Analytics
- **LIFO Position Accounting** - Matches Webull broker dashboard calculations
- **Real-time P&L Tracking** - Cumulative and daily returns visualization
- **Win/Loss Analysis** - Round-trip win rates, profit factors, streaks
- **Risk Metrics** - Max drawdown, hold times, position sizing
- **Trade Efficiency** - Return skewness, volatility, average returns
- **Behavioral Insights** - Trading frequency, long/short bias, diversification

### AI-Powered Suggestions
- **GPT-4 Integration** - Personalized trading recommendations
- **Symbol-Specific Analysis** - Identifies best/worst performers
- **Actionable Insights** - Concrete position sizing and risk management advice
- **Typing Animation** - Engaging UI for AI responses

### Professional UI
- **Modern Dark Theme** - Built with TailwindCSS
- **Interactive Charts** - Recharts with break-even reference lines
- **Responsive Design** - Works on desktop, tablet, and mobile
- **Real-time Metrics** - Auto-updating performance cards
- **Scrollable Tables** - Efficient symbol breakdown with search/sort

## 📦 Tech Stack

**Backend:**
- FastAPI (Python 3.10+)
- Pandas for data processing
- OpenAI GPT-4 API
- LIFO accounting engine
- US/Eastern timezone handling

**Frontend:**
- React 18 with Vite
- TailwindCSS for styling
- Recharts for visualizations
- Framer Motion for animations
- Lucide React icons

## 🛠️ Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- OpenAI API key (for AI suggestions)

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend Setup
```bash
cd frontend
npm install
```

## 🔑 Configuration

Create a `.env` file in the backend directory:
```bash
OPENAI_API_KEY=your_openai_api_key_here
PORT=8003
```

## 🚀 Running the Application

### Start Backend
```bash
cd backend
source venv/bin/activate
uvicorn main_webull:app --reload --port 8003
```

### Start Frontend
```bash
cd frontend
npm run dev
```

Visit `http://localhost:5173` to see the dashboard.

## 📊 Usage

1. **Upload CSV** - Upload your Webull trading history CSV
2. **View Analytics** - Explore comprehensive performance metrics
3. **AI Insights** - Get personalized suggestions to improve profitability
4. **Export Data** - Download symbol breakdown as CSV

### Supported CSV Format
- Webull Orders Records (equities)
- Columns: Symbol, Side, Qty, Price, Time, etc.
- US/Eastern timezone

## 🎯 Key Metrics

### Performance Overview
- Total P&L
- Average Monthly Return
- Sharpe Ratio
- Expectancy per trade

### Win/Loss Analysis
- Win Rate (round-trip)
- Average Win vs Average Loss
- Profit Factor
- Win/Loss Streaks

### Trade Efficiency
- Average Hold Time
- Average Trade Size
- Return Skewness
- P&L Volatility

### Trading Behavior
- Long/Short Distribution
- Symbol Concentration
- Trade Frequency
- Diversification Score

## 🤖 AI Suggestions

The AI analyzes your:
- Overall performance metrics
- Top 5 winning symbols
- Top 5 losing symbols
- Trading patterns and behavior

And provides:
- Specific symbol recommendations
- Position sizing advice
- Risk management strategies
- Pattern-based insights

## 📁 Project Structure

```
windsurf-project/
├── backend/
│   ├── services/
│   │   ├── ingest.py           # CSV parsing
│   │   ├── accounting_lifo.py  # LIFO engine
│   │   └── metrics.py          # Calculations
│   ├── main_webull.py          # FastAPI app
│   └── demo_data.py            # Demo endpoint
├── frontend/
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── pages/              # Dashboard & Upload
│   │   └── App.jsx
│   └── public/
└── README.md
```

## 🔒 Security

- API keys stored in environment variables
- `.env` files excluded from Git
- No sensitive data in commits
- CORS configured for local development

## 📝 License

© 2025 Jones Software & Data - All Rights Reserved

## 🤝 Contributing

This is a private MVP. For inquiries, contact the development team.

## 📧 Support

For issues or questions, please open a GitHub issue.

---

**Built with ❤️ by Jones Software & Data**
