# 📊 Jones Trading Performance Dashboard

A professional-grade web application for analyzing trading performance with interactive charts, comprehensive metrics, and beautiful dark-mode UI.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## 🎯 Features

### Core Functionality
- **CSV Upload & Parsing** - Automatic detection and standardization of broker formats (Webull, TD Ameritrade, Interactive Brokers)
- **Interactive P&L Chart** - Real-time visualization with timeframe selectors (Week, Month, YTD, All Time)
- **Comprehensive Metrics** - 12+ key performance indicators including Sharpe Ratio, Win Rate, Max Drawdown
- **Per-Symbol Breakdown** - Detailed analysis of each traded symbol with sortable tables
- **Data Export** - Download cleaned data and results as CSV

### Analytics Provided
- **Performance**: Total P&L, Avg Monthly Return, Sharpe Ratio, Expectancy
- **Win/Loss**: Win Rate %, Avg Win/Loss $, Profit Factor
- **Risk**: Max Drawdown %, Avg Hold Length, Total Trades
- **Per-Stock**: Symbol-level P&L and trade statistics

## 🛠️ Tech Stack

### Frontend
- **React 18** with Vite - Fast, modern development
- **TailwindCSS** - Utility-first styling with custom dark theme
- **Recharts** - Interactive financial charts
- **Framer Motion** - Smooth animations and transitions
- **Lucide React** - Beautiful icon library
- **React Dropzone** - Drag-and-drop file upload

### Backend
- **FastAPI** - High-performance Python API framework
- **Pandas** - Data manipulation and analysis
- **NumPy** - Statistical calculations
- **Uvicorn** - ASGI server

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.11+
- pip

### Installation

1. **Clone the repository**
```bash
cd /Users/jakejones/Desktop/Software/Financial_Dashboard/CascadeProjects/windsurf-project
```

2. **Backend Setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Frontend Setup**
```bash
cd ../frontend
npm install
```

### Running the Application

1. **Start the Backend** (Terminal 1)
```bash
cd backend
source venv/bin/activate
python main.py
# Backend runs on http://localhost:8000
```

2. **Start the Frontend** (Terminal 2)
```bash
cd frontend
npm run dev
# Frontend runs on http://localhost:5173
```

3. **Open your browser**
Navigate to `http://localhost:5173`

## 📁 Project Structure

```
windsurf-project/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   ├── Dockerfile          # Backend container config
│   └── .env.example        # Environment variables template
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   │   ├── Header.jsx
│   │   │   ├── MetricCard.jsx
│   │   │   ├── PnLChart.jsx
│   │   │   ├── SymbolTable.jsx
│   │   │   └── FileUpload.jsx
│   │   ├── pages/          # Page components
│   │   │   ├── Upload.jsx
│   │   │   └── Dashboard.jsx
│   │   ├── App.jsx         # Main app component
│   │   ├── main.jsx        # Entry point
│   │   └── index.css       # Global styles
│   ├── package.json        # Node dependencies
│   ├── vite.config.js      # Vite configuration
│   ├── tailwind.config.js  # Tailwind configuration
│   └── index.html          # HTML template
├── sample_data/
│   └── sample_trades.csv   # Example trading data
└── README.md
```

## 📊 CSV Format

Your CSV should include these columns (column names are flexible):

| Column | Aliases | Required | Description |
|--------|---------|----------|-------------|
| Date | date, datetime, time | ✅ | Trade execution date |
| Symbol | symbol, ticker | ✅ | Stock ticker symbol |
| Quantity | quantity, qty | ✅ | Number of shares |
| Price | price, execution_price | ✅ | Execution price per share |
| Side | side, action, type | ✅ | Buy or Sell |
| Fees | fees, commission | ❌ | Commission/fees (defaults to 0) |
| Realized_PnL | pnl, profit_loss, P&L | ❌ | Profit/Loss (auto-calculated if missing) |

### Example CSV
```csv
Date,Symbol,Quantity,Price,Side,Fees,Realized_PnL
2024-01-05,AAPL,100,185.50,Buy,1.00,-18551.00
2024-01-08,AAPL,100,189.25,Sell,1.00,18923.00
2024-01-10,TSLA,50,238.45,Buy,1.00,-11923.50
```

## 🎨 Design System

### Color Palette
- **Background**: `#0B0C10` - Deep dark base
- **Primary**: `#FFD700` - Jones gold accent
- **Secondary**: `#1F2833` - Card backgrounds
- **Text**: `#C5C6C7` - Primary text
- **Text Dark**: `#8B8C8D` - Secondary text

### Typography
- **Sans**: Inter - Clean, modern UI text
- **Mono**: Roboto Mono - Data tables and numbers

## 📈 Metrics Explained

### Sharpe Ratio
Risk-adjusted return metric. Higher is better (>1 is good, >2 is excellent).
```
Sharpe = (Mean Return - Risk-Free Rate) / StdDev(Returns) * √252
```

### Profit Factor
Ratio of gross profit to gross loss. Values >1 indicate profitability.
```
Profit Factor = Total Profit / Total Loss
```

### Expectancy
Expected value per trade in dollars.
```
Expectancy = (Win% × AvgWin) - (Loss% × AvgLoss)
```

### Max Drawdown
Largest peak-to-trough decline in equity curve (as percentage).

## 🚢 Deployment

### Railway.app (Recommended)

1. **Backend Deployment**
```bash
cd backend
railway login
railway init
railway up
```

2. **Frontend Deployment**
```bash
cd frontend
npm run build
railway up
```

### Docker Deployment

```bash
# Backend
cd backend
docker build -t trading-dashboard-backend .
docker run -p 8000:8000 trading-dashboard-backend

# Frontend
cd frontend
npm run build
# Serve the dist/ folder with nginx or similar
```

## 🔮 Future Enhancements (Phase 2)

- [ ] User authentication (OAuth, email)
- [ ] Save and compare multiple uploads
- [ ] Direct broker API integration
- [ ] Benchmark comparison (vs SPY)
- [ ] Strategy tagging and filtering
- [ ] Mobile app (React Native)
- [ ] ML-powered performance predictions

## 🤝 Contributing

This is a personal project by Jake Jones. For suggestions or issues, please contact directly.

## 📄 License

MIT License - See LICENSE file for details

## 👤 Author

**Jake Jones**  
Jones Software & Data  
October 2025

---

Built with ❤️ using React, FastAPI, and TailwindCSS
