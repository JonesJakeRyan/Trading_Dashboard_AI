# AI Coach - Input Data Example (Creator Demo Trades)

This document shows **exactly** what data we send to OpenAI to generate AI coaching insights, using the creator's demo trading data.

---

## Step 1: Fetch Aggregate Metrics from Database

**Query:** Get aggregate metrics for the creator's demo account (account_id = None)

**Database Result:**
```python
{
    "cumulative_pnl": 1335.19,      # Total realized P&L
    "total_trades": 1110,            # Number of closed lots
    "win_rate": 0.5586,              # 55.86% as decimal
    "avg_gain": 22.72,               # Average winning trade
    "avg_loss": -23.49,              # Average losing trade
    "profit_factor": 1.23,           # Total gains / Total losses
    "best_symbol": "TQQQ",           # Best performing ticker
    "worst_symbol": "SQQQ",          # Worst performing ticker
    "best_weekday": "Monday",        # Best day of week
    "worst_weekday": "Tuesday"       # Worst day of week
}
```

---

## Step 2: Transform Data for AI Service

**Transformation:** Convert win_rate to percentage (multiply by 100)

```python
metrics = {
    "cumulative_pnl": 1335.19,
    "total_trades": 1110,
    "win_rate": 55.86,               # Converted to percentage
    "profit_factor": 1.23,
    "avg_gain": 22.72,
    "avg_loss": -23.49,
    "best_symbol": "TQQQ",
    "worst_symbol": "SQQQ",
    "best_weekday": "Monday",
    "worst_weekday": "Tuesday"
}
```

---

## Step 3: Build OpenAI Prompt

### System Prompt (Sets AI Behavior):
```
You are a trading performance analyst. Analyze trading metrics and provide 
educational insights about patterns and risks. NEVER provide specific ticker 
recommendations or trade calls. Focus on behavioral patterns, risk management, 
and general trading discipline observations.
```

### User Prompt (Actual Data):
```
Analyze the following trading performance metrics and provide insights:

**Performance Summary:**
- Cumulative Realized P&L: $1,335.19
- Total Closed Trades: 1110
- Win Rate: 55.9%
- Profit Factor: 1.23
- Average Gain: $22.72
- Average Loss: $-23.49
- Best Performing Symbol: TQQQ
- Worst Performing Symbol: SQQQ
- Best Trading Day: Monday
- Worst Trading Day: Tuesday

Provide:
1. A brief summary (2-3 sentences) of overall performance
2. 2-3 pattern insights based on the metrics (what patterns do you observe?)
3. 2-3 risk notes (what risks or concerns should be monitored?)
4. 3-4 actionable recommendations (general trading discipline, not specific trades)

Remember: NO specific ticker recommendations. Focus on behavioral patterns and risk management.
```

---

## Step 4: OpenAI API Call Configuration

**Model:** `gpt-4o-mini` (cost-efficient)

**Parameters:**
```python
{
    "model": "gpt-4o-mini",
    "temperature": 0.7,              # Balanced creativity
    "max_tokens": 1500,              # Limit response length
    "response_format": {
        "type": "json_schema",       # Force JSON output
        "json_schema": {
            "name": "trading_insights",
            "strict": True,          # Enforce exact schema
            "schema": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "pattern_insights": [...],
                    "risk_notes": [...],
                    "top_actions": [...]
                },
                "required": ["summary", "pattern_insights", "risk_notes", "top_actions"]
            }
        }
    }
}
```

---

## Step 5: Expected JSON Response Schema

OpenAI **must** return data in this exact format:

```json
{
  "summary": "string (2-3 sentences)",
  "pattern_insights": [
    {
      "title": "string",
      "evidence_metric": "string (reference to specific metric)",
      "why_it_matters": "string (explanation)"
    }
  ],
  "risk_notes": [
    {
      "title": "string",
      "trigger_condition": "string (what triggers this risk)",
      "mitigation_tip": "string (how to address it)"
    }
  ],
  "top_actions": [
    {
      "priority": integer (1-4),
      "action": "string (actionable recommendation)"
    }
  ]
}
```

---

## Step 6: Actual Response (Creator Demo Data)

**OpenAI Response (or Fallback if no API key):**

```json
{
  "summary": "Your trading performance shows positive results with a 55.9% win rate and $1,335.19 cumulative P&L. Continue monitoring your metrics to identify areas for improvement.",
  
  "pattern_insights": [
    {
      "title": "Win Rate Analysis",
      "evidence_metric": "Current win rate: 55.9%",
      "why_it_matters": "Win rate above 50% suggests more winning trades than losing trades, but should be considered alongside profit factor."
    },
    {
      "title": "Profit Factor Assessment",
      "evidence_metric": "Profit factor: 1.23",
      "why_it_matters": "A profit factor above 1.0 indicates that total gains exceed total losses, which is essential for long-term profitability."
    }
  ],
  
  "risk_notes": [
    {
      "title": "Position Sizing Consistency",
      "trigger_condition": "Large variation in trade sizes can increase risk",
      "mitigation_tip": "Consider maintaining consistent position sizes relative to account size to manage risk effectively."
    },
    {
      "title": "Drawdown Monitoring",
      "trigger_condition": "Extended losing streaks can impact account equity",
      "mitigation_tip": "Set maximum drawdown limits and review trading strategy if limits are approached."
    }
  ],
  
  "top_actions": [
    {
      "priority": 1,
      "action": "Review your best and worst performing symbols to identify what's working and what isn't."
    },
    {
      "priority": 2,
      "action": "Analyze your trading patterns by day of week to optimize timing."
    },
    {
      "priority": 3,
      "action": "Maintain a trading journal to document the reasoning behind each trade."
    },
    {
      "priority": 4,
      "action": "Consider setting profit targets and stop losses for each position to manage risk."
    }
  ]
}
```

---

## Key Insights from Creator's Trading Data

### What the AI Sees:

1. **Overall Performance: Profitable**
   - $1,335.19 cumulative P&L (positive)
   - 55.9% win rate (above 50%)
   - 1,110 closed trades (high volume)

2. **Risk/Reward Balance: Slightly Favorable**
   - Profit Factor: 1.23 (gains exceed losses by 23%)
   - Average Gain: $22.72
   - Average Loss: $-23.49
   - **Observation:** Losses are slightly larger than gains, but win rate compensates

3. **Symbol Performance: Leveraged ETFs**
   - Best: TQQQ (3x leveraged Nasdaq bull)
   - Worst: SQQQ (3x leveraged Nasdaq bear)
   - **Pattern:** Trading leveraged instruments with directional bias

4. **Timing Patterns:**
   - Best Day: Monday (start of week strength)
   - Worst Day: Tuesday (potential reversal day)
   - **Observation:** Day-of-week effect present

---

## What the AI Does NOT See

Per PRD requirements, we intentionally **DO NOT** send:

❌ Individual trade details (dates, prices, quantities)  
❌ Intraday price movements  
❌ Order types (market, limit, stop)  
❌ Account balance or position sizes  
❌ Broker information  
❌ User personal information  

**Why?** 
- Privacy: No PII or sensitive account data
- Focus: AI analyzes patterns, not individual trades
- Compliance: No specific trade recommendations
- Performance: Smaller payload = faster response

---

## Fallback Response (No OpenAI API Key)

If `OPENAI_API_KEY` is not set, the system generates an intelligent fallback using the same metrics:

**Logic:**
```python
if cumulative_pnl > 0 and win_rate > 50:
    performance = "positive"
elif cumulative_pnl < 0:
    performance = "negative"
else:
    performance = "mixed"

# Generate insights based on performance level
# Use metric thresholds to create relevant observations
```

**Result:** Users still get valuable insights even without OpenAI integration.

---

## Summary: Data Flow

```
Creator CSV (1,110 trades)
    ↓
FIFO Engine (lot matching)
    ↓
Aggregate Metrics (10 key metrics)
    ↓
AI Service (transform + prompt)
    ↓
OpenAI API (JSON mode, strict schema)
    ↓
Validated Response (Pydantic models)
    ↓
Frontend Display (typing animation)
```

**Total Data Sent to OpenAI:** ~500 characters (just the metrics, no raw trades)

**Response Size:** ~1,500-2,000 characters (structured insights)

**Cost per Request:** ~$0.001-0.002 (GPT-4-mini pricing)

---

## Testing the Input

You can see the exact prompt by running:

```bash
# Get the metrics
curl 'http://localhost:8000/api/demo/metrics?timeframe=ALL'

# Get the AI insights (see what OpenAI returns)
curl 'http://localhost:8000/api/demo/ai/coach?timeframe=ALL'
```

Or check the logs when the backend processes a request:

```
INFO: AI Coach request - account_id=None, timeframe=ALL
INFO: Generating AI insights
INFO: OpenAI response received - tokens used: 450
```
