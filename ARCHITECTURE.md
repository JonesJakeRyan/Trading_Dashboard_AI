# 🏗️ System Architecture

## Overview

The Trading Performance Dashboard follows a modern client-server architecture with a React frontend and FastAPI backend.

```
┌─────────────────────────────────────────────────────────────┐
│                         USER BROWSER                         │
│                     http://localhost:5173                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/REST
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      REACT FRONTEND                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Components Layer                                     │  │
│  │  • Header (Navigation)                                │  │
│  │  • FileUpload (Drag & Drop)                          │  │
│  │  • MetricCard (Animated Cards)                       │  │
│  │  • PnLChart (Interactive Charts)                     │  │
│  │  • SymbolTable (Data Table)                          │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Pages Layer                                          │  │
│  │  • Upload Page (File Upload & Instructions)          │  │
│  │  • Dashboard Page (Analytics Display)                │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  State Management                                     │  │
│  │  • React Hooks (useState, useEffect)                 │  │
│  │  • React Router (Navigation)                         │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Styling                                              │  │
│  │  • TailwindCSS (Utility Classes)                     │  │
│  │  • Framer Motion (Animations)                        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Axios HTTP Client
                              │ POST /api/upload
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                         │
│                   http://localhost:8000                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  API Endpoints                                        │  │
│  │  • GET  /           (Health Check)                   │  │
│  │  • POST /api/upload (Upload & Analyze)               │  │
│  │  • POST /api/filter (Filter Trades)                  │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  CSV Parser                                           │  │
│  │  • Column name standardization                       │  │
│  │  • Multi-broker format detection                     │  │
│  │  • Data validation & cleaning                        │  │
│  │  • Type conversion                                    │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  TradeAnalyzer (Analytics Engine)                    │  │
│  │  • Performance Metrics Calculator                    │  │
│  │  • Win/Loss Statistics                               │  │
│  │  • Risk Metrics (Sharpe, Drawdown)                   │  │
│  │  • Per-Symbol Breakdown                              │  │
│  │  • P&L Series Generation                             │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Data Processing (Pandas/NumPy)                      │  │
│  │  • DataFrame operations                               │  │
│  │  • Statistical calculations                          │  │
│  │  • Time series analysis                              │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### 1. File Upload Flow

```
User Selects CSV
      │
      ▼
FileUpload Component (Drag & Drop)
      │
      ▼
Upload.jsx (Page)
      │
      ▼
Axios POST to /api/upload
      │
      ▼
FastAPI Endpoint Handler
      │
      ▼
CSV Parser (parse_csv function)
      │
      ├─► Column Mapping
      ├─► Data Validation
      ├─► Type Conversion
      └─► Duplicate Removal
      │
      ▼
TradeAnalyzer Class
      │
      ├─► calculate_all_metrics()
      │   ├─► get_performance_metrics()
      │   ├─► get_win_loss_metrics()
      │   ├─► get_risk_metrics()
      │   ├─► get_per_symbol_breakdown()
      │   ├─► get_pnl_series()
      │   └─► get_equity_curve()
      │
      ▼
JSON Response
      │
      ▼
Frontend State Update (setMetrics)
      │
      ▼
Navigate to Dashboard
      │
      ▼
Dashboard.jsx Renders Analytics
```

### 2. Dashboard Rendering Flow

```
Dashboard.jsx receives metrics
      │
      ├─► Performance Metrics
      │   └─► 4x MetricCard Components
      │
      ├─► Win/Loss Metrics
      │   └─► 4x MetricCard Components
      │
      ├─► Risk Metrics
      │   └─► 3x MetricCard Components
      │
      ├─► P&L Chart
      │   └─► PnLChart Component
      │       ├─► Timeframe Filtering
      │       ├─► Chart Type Toggle
      │       └─► Recharts AreaChart
      │
      └─► Symbol Breakdown
          └─► SymbolTable Component
              ├─► Search Filtering
              ├─► Column Sorting
              └─► CSV Export
```

---

## Component Hierarchy

```
App.jsx
├── Router
│   ├── Header (always visible)
│   │   ├── Logo/Title
│   │   └── Navigation Links
│   │
│   └── Routes
│       ├── Route: "/" → Upload.jsx
│       │   ├── FileUpload Component
│       │   ├── Success/Error Messages
│       │   └── Instructions Section
│       │
│       └── Route: "/dashboard" → Dashboard.jsx
│           ├── Header Section
│           │   ├── Title
│           │   └── Upload New Button
│           │
│           ├── Performance Section
│           │   └── 4x MetricCard
│           │
│           ├── Win/Loss Section
│           │   └── 4x MetricCard
│           │
│           ├── Risk Section
│           │   └── 3x MetricCard
│           │
│           ├── PnLChart Component
│           │   ├── Timeframe Buttons
│           │   ├── Chart Type Toggle
│           │   └── Recharts AreaChart
│           │
│           └── SymbolTable Component
│               ├── Search Input
│               ├── Export Button
│               └── Data Table
```

---

## Technology Stack Details

### Frontend Stack

```
React 18.2
├── Vite 5.0 (Build Tool)
│   ├── Fast HMR
│   ├── Optimized builds
│   └── ES modules
│
├── React Router 6.20 (Navigation)
│   ├── BrowserRouter
│   ├── Routes/Route
│   └── useNavigate hook
│
├── TailwindCSS 3.3 (Styling)
│   ├── Custom color palette
│   ├── Dark mode by default
│   └── Responsive utilities
│
├── Recharts 2.10 (Charts)
│   ├── AreaChart
│   ├── LineChart
│   ├── Custom tooltips
│   └── Responsive containers
│
├── Framer Motion 10.16 (Animations)
│   ├── Component animations
│   ├── Page transitions
│   └── Gesture handling
│
├── Lucide React 0.294 (Icons)
│   ├── 1000+ icons
│   ├── Tree-shakeable
│   └── Customizable
│
├── React Dropzone 14.2 (File Upload)
│   ├── Drag & drop
│   ├── File validation
│   └── Preview support
│
└── Axios 1.6 (HTTP Client)
    ├── Promise-based
    ├── Request/response interceptors
    └── Automatic JSON transformation
```

### Backend Stack

```
FastAPI 0.104.1
├── Uvicorn 0.24 (ASGI Server)
│   ├── High performance
│   ├── WebSocket support
│   └── Auto-reload in dev
│
├── Pandas 2.1.3 (Data Analysis)
│   ├── DataFrame operations
│   ├── Time series handling
│   ├── Groupby aggregations
│   └── CSV parsing
│
├── NumPy 1.26.2 (Numerical Computing)
│   ├── Array operations
│   ├── Statistical functions
│   └── Mathematical operations
│
├── Pydantic 2.5 (Data Validation)
│   ├── Type checking
│   ├── Schema validation
│   └── JSON serialization
│
└── Python Multipart 0.0.6 (File Upload)
    └── Multipart form data handling
```

---

## API Contract

### POST /api/upload

**Request:**
```http
POST /api/upload HTTP/1.1
Content-Type: multipart/form-data

file: [CSV File]
```

**Response:**
```json
{
  "success": true,
  "filename": "sample_trades.csv",
  "total_rows": 30,
  "metrics": {
    "performance": {
      "total_pnl": 12500.00,
      "avg_monthly_return": 2500.00,
      "sharpe_ratio": 1.85,
      "expectancy": 416.67
    },
    "win_loss": {
      "win_rate": 73.33,
      "avg_win": 850.00,
      "avg_loss": -425.00,
      "profit_factor": 2.45
    },
    "risk": {
      "max_drawdown": 8.50,
      "avg_hold_length": 4.5,
      "total_trades": 30
    },
    "per_symbol": [
      {
        "symbol": "NVDA",
        "num_trades": 3,
        "total_pnl": 3500.00,
        "avg_return_pct": 5.2
      }
    ],
    "pnl_series": [
      {
        "date": "2024-01-05",
        "daily_pnl": 372.00,
        "cumulative_pnl": 372.00
      }
    ],
    "equity_curve": [
      {
        "date": "2024-01-05",
        "equity": 10372.00
      }
    ]
  }
}
```

---

## State Management

### Frontend State

```javascript
// App.jsx - Global State
const [metrics, setMetrics] = useState(null)
const [fileName, setFileName] = useState(null)

// Upload.jsx - Local State
const [isLoading, setIsLoading] = useState(false)
const [error, setError] = useState(null)
const [success, setSuccess] = useState(false)

// Dashboard.jsx - Derived State
const { performance, win_loss, risk, per_symbol, pnl_series } = metrics

// PnLChart.jsx - Component State
const [timeframe, setTimeframe] = useState('all')
const [chartType, setChartType] = useState('cumulative')

// SymbolTable.jsx - Component State
const [searchTerm, setSearchTerm] = useState('')
const [sortConfig, setSortConfig] = useState({ key: 'total_pnl', direction: 'desc' })
```

---

## Performance Optimizations

### Frontend
- **Code Splitting**: React.lazy() for route-based splitting
- **Memoization**: useMemo for expensive calculations
- **Debouncing**: Search input debouncing
- **Virtual Scrolling**: For large symbol tables (future)
- **Image Optimization**: Lazy loading images
- **Bundle Size**: Tree-shaking unused code

### Backend
- **Vectorized Operations**: Pandas vectorization for speed
- **Efficient Parsing**: Streaming CSV parsing for large files
- **Caching**: Response caching (future with Redis)
- **Connection Pooling**: Database connection pooling (Phase 2)
- **Async Operations**: FastAPI async endpoints

---

## Security Considerations

### Current Implementation
- CORS configuration for allowed origins
- File type validation (CSV only)
- Input sanitization in CSV parser
- Error handling without exposing internals

### Future Enhancements (Phase 2)
- JWT authentication
- Rate limiting
- File size limits
- Virus scanning for uploads
- SQL injection prevention (when DB added)
- XSS protection
- HTTPS enforcement

---

## Scalability Considerations

### Current Capacity
- Handles CSVs up to ~10,000 rows efficiently
- Single-server deployment
- In-memory processing

### Future Scaling (Phase 2)
- **Horizontal Scaling**: Load balancer + multiple backend instances
- **Database**: PostgreSQL for persistent storage
- **Caching**: Redis for frequently accessed data
- **CDN**: CloudFlare for static assets
- **Queue System**: Celery for background processing
- **File Storage**: S3 for uploaded CSVs

---

## Error Handling

### Frontend
```javascript
try {
  const response = await axios.post('/api/upload', formData)
  // Handle success
} catch (err) {
  // Display user-friendly error
  setError(err.response?.data?.detail || 'Upload failed')
}
```

### Backend
```python
try:
    df = parse_csv(content_str)
    analyzer = TradeAnalyzer(df)
    metrics = analyzer.calculate_all_metrics()
    return JSONResponse(content=metrics)
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    logger.error(f"Unexpected error: {str(e)}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

---

## Development Workflow

```
Local Development
      │
      ├─► Backend (port 8000)
      │   ├─► Auto-reload on file changes
      │   ├─► Interactive API docs at /docs
      │   └─► Logging to console
      │
      └─► Frontend (port 5173)
          ├─► Hot Module Replacement (HMR)
          ├─► Fast refresh
          └─► Proxy API requests to backend

Production Build
      │
      ├─► Backend
      │   ├─► Gunicorn with multiple workers
      │   ├─► Environment-based configuration
      │   └─► Production logging
      │
      └─► Frontend
          ├─► Optimized bundle (npm run build)
          ├─► Minified assets
          ├─► Code splitting
          └─► Static file serving
```

---

## Monitoring & Logging

### Backend Logging
```python
import logging

logger = logging.getLogger(__name__)
logger.info(f"Successfully analyzed {len(df)} trades")
logger.error(f"Error parsing CSV: {str(e)}")
```

### Frontend Logging
```javascript
console.log('Upload successful:', response.data)
console.error('Upload error:', err)
```

### Future Monitoring (Phase 2)
- Application Performance Monitoring (APM)
- Error tracking (Sentry)
- Analytics (Google Analytics, Mixpanel)
- Uptime monitoring (UptimeRobot)

---

## Testing Strategy

### Backend Testing
```python
# pytest tests/test_analyzer.py
def test_performance_metrics():
    df = create_sample_dataframe()
    analyzer = TradeAnalyzer(df)
    metrics = analyzer.get_performance_metrics()
    assert metrics['total_pnl'] > 0
```

### Frontend Testing
```javascript
// Vitest + React Testing Library
describe('MetricCard', () => {
  it('renders positive values in green', () => {
    render(<MetricCard value={100} />)
    expect(screen.getByText('$100')).toHaveClass('text-green-400')
  })
})
```

---

## Deployment Architecture

```
Production Environment
      │
      ├─► Railway/Render Platform
      │   ├─► Automatic deployments from Git
      │   ├─► Environment variables
      │   ├─► SSL certificates
      │   └─► Custom domains
      │
      ├─► Backend Service
      │   ├─► Docker container
      │   ├─► Health checks
      │   └─► Auto-scaling (future)
      │
      └─► Frontend Service
          ├─► Static site hosting
          ├─► CDN distribution
          └─► Gzip compression
```

---

This architecture provides a solid foundation for the MVP while allowing for future enhancements and scaling as needed.
