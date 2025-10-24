# 🚀 Webull Broker Matching - Quick Start

## ⚡ Get Started in 2 Minutes

### 1. Start the Server
```bash
cd backend
uvicorn main_webull:app --reload --port 8003
```

### 2. Test with Your Data
```bash
# Single file
curl -X POST http://localhost:8003/api/upload \
  -F "file=@Webull_Orders_Records.csv"

# Combined (stocks + options)
curl -X POST http://localhost:8003/api/upload/combined \
  -F "equities_file=@Webull_Orders_Records.csv" \
  -F "options_file=@Webull_Orders_Records_Options.csv"
```

### 3. View Results
```
http://localhost:8003/docs
```

---

## 📊 Your Actual Results

**Equities**: 241 trades, -$1,736.39 P&L, 45.2% win rate  
**Options**: 19 trades, $211.00 P&L  
**Combined**: 260 trades, -$1,525.39 P&L, 45.4% win rate

---

## 🎯 Key Features

- ✅ **Average-cost accounting** (matches Webull)
- ✅ **No fees** in P&L
- ✅ **US/Eastern timezone**
- ✅ **Round-trip trades** (flat → flat)
- ✅ **Options support** (100x multiplier)

---

## 📚 Documentation

- **WEBULL_MATCHING_README.md** - Complete methodology
- **WEBULL_IMPLEMENTATION_SUMMARY.md** - Implementation details
- **GET /api/docs/accounting** - API documentation

---

## ✅ Ready!

Your Webull broker matching system is live on **port 8003**! 🎉
