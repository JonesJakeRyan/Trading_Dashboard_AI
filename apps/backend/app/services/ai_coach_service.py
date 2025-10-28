"""
AI Coach Service - OpenAI integration for generating trading insights.

Uses OpenAI JSON mode to generate deterministic insights based on trading metrics.
Includes retry logic and fallback responses per PRD requirements.
"""
import logging
import json
import os
from typing import Dict, Any, Optional
from openai import OpenAI
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


class PatternInsight(BaseModel):
    title: str
    evidence_metric: str
    why_it_matters: str


class RiskNote(BaseModel):
    title: str
    trigger_condition: str
    mitigation_tip: str


class TopAction(BaseModel):
    priority: int
    action: str


class AICoachResponse(BaseModel):
    summary: str
    pattern_insights: list[PatternInsight]
    risk_notes: list[RiskNote]
    top_actions: list[TopAction]


class AICoachService:
    """Service for generating AI coaching insights using OpenAI."""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not set - AI Coach will use fallback responses")
            self.client = None
        else:
            self.client = OpenAI(api_key=self.api_key)
        
        self.model = "gpt-4o-mini"  # Using GPT-4 mini for cost efficiency
        self.max_retries = 1  # Per PRD: retry once on failure
    
    def generate_insights(
        self,
        metrics: Dict[str, Any],
        symbol_summary: Optional[Dict[str, Any]] = None
    ) -> AICoachResponse:
        """
        Generate AI insights based on trading metrics.
        
        Args:
            metrics: Aggregate trading metrics (P&L, win rate, etc.)
            symbol_summary: Optional symbol-level performance data
        
        Returns:
            AICoachResponse with insights, patterns, risks, and actions
        """
        logger.info("Generating AI insights")
        
        # If no OpenAI client, return fallback immediately
        if not self.client:
            logger.warning("No OpenAI client - returning fallback response")
            return self._get_fallback_response(metrics)
        
        # Try to get OpenAI response with retry
        for attempt in range(self.max_retries + 1):
            try:
                logger.info(f"OpenAI attempt {attempt + 1}/{self.max_retries + 1}")
                response = self._call_openai(metrics, symbol_summary)
                
                # Validate response against schema
                validated_response = AICoachResponse(**response)
                logger.info("Successfully generated and validated AI insights")
                return validated_response
                
            except ValidationError as e:
                logger.error(f"Schema validation failed on attempt {attempt + 1}: {str(e)}")
                if attempt < self.max_retries:
                    logger.info("Retrying OpenAI call...")
                    continue
                else:
                    logger.warning("Max retries reached - returning fallback")
                    return self._get_fallback_response(metrics)
            
            except Exception as e:
                logger.error(f"OpenAI call failed on attempt {attempt + 1}: {str(e)}")
                if attempt < self.max_retries:
                    logger.info("Retrying OpenAI call...")
                    continue
                else:
                    logger.warning("Max retries reached - returning fallback")
                    return self._get_fallback_response(metrics)
        
        # Should never reach here, but return fallback just in case
        return self._get_fallback_response(metrics)
    
    def _call_openai(
        self,
        metrics: Dict[str, Any],
        symbol_summary: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Call OpenAI API in JSON mode.
        
        Per PRD: No ticker advice or recommendations allowed.
        """
        # Build prompt
        prompt = self._build_prompt(metrics, symbol_summary)
        
        # Define JSON schema for response_format
        response_schema = {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "pattern_insights": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "evidence_metric": {"type": "string"},
                            "why_it_matters": {"type": "string"}
                        },
                        "required": ["title", "evidence_metric", "why_it_matters"],
                        "additionalProperties": False
                    }
                },
                "risk_notes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "trigger_condition": {"type": "string"},
                            "mitigation_tip": {"type": "string"}
                        },
                        "required": ["title", "trigger_condition", "mitigation_tip"],
                        "additionalProperties": False
                    }
                },
                "top_actions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "priority": {"type": "integer"},
                            "action": {"type": "string"}
                        },
                        "required": ["priority", "action"],
                        "additionalProperties": False
                    }
                }
            },
            "required": ["summary", "pattern_insights", "risk_notes", "top_actions"],
            "additionalProperties": False
        }
        
        # Call OpenAI with JSON mode
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a trading performance analyst. Analyze trading metrics and provide "
                        "educational insights about patterns and risks. NEVER provide specific ticker "
                        "recommendations or trade calls. Focus on behavioral patterns, risk management, "
                        "and general trading discipline observations."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "trading_insights",
                    "strict": True,
                    "schema": response_schema
                }
            },
            temperature=0.7,
            max_tokens=1500
        )
        
        # Parse JSON response
        response_text = completion.choices[0].message.content
        response_data = json.loads(response_text)
        
        logger.info(f"OpenAI response received - tokens used: {completion.usage.total_tokens}")
        
        return response_data
    
    def _build_prompt(
        self,
        metrics: Dict[str, Any],
        symbol_summary: Optional[Dict[str, Any]]
    ) -> str:
        """Build the prompt for OpenAI based on metrics."""
        
        # Extract all metrics
        cumulative_pnl = metrics.get('cumulative_pnl', 0)
        win_rate = metrics.get('win_rate', 0)
        profit_factor = metrics.get('profit_factor', 0)
        total_trades = metrics.get('total_trades', 0)
        avg_gain = metrics.get('avg_gain', 0)
        avg_loss = metrics.get('avg_loss', 0)
        best_symbol = metrics.get('best_symbol', 'N/A')
        worst_symbol = metrics.get('worst_symbol', 'N/A')
        best_weekday = metrics.get('best_weekday', 'N/A')
        worst_weekday = metrics.get('worst_weekday', 'N/A')
        
        # Enhanced metrics
        avg_hold_time = metrics.get('avg_holding_time_minutes', 0)
        avg_hold_winners = metrics.get('avg_holding_time_winners', 0)
        avg_hold_losers = metrics.get('avg_holding_time_losers', 0)
        quick_flip_rate = metrics.get('quick_flip_rate', 0)
        
        top_3_symbols = metrics.get('top_3_symbols', [])
        concentration_ratio = metrics.get('concentration_ratio', 0)
        leveraged_pct = metrics.get('leveraged_etf_pct', 0)
        unique_symbols = metrics.get('total_unique_symbols', 0)
        
        current_streak = metrics.get('current_streak', 0)
        longest_win_streak = metrics.get('longest_win_streak', 0)
        longest_loss_streak = metrics.get('longest_loss_streak', 0)
        
        best_hour = metrics.get('best_hour', 'N/A')
        best_hour_pnl = metrics.get('best_hour_avg_pnl', 0)
        worst_hour = metrics.get('worst_hour', 'N/A')
        worst_hour_pnl = metrics.get('worst_hour_avg_pnl', 0)
        best_month = metrics.get('best_month', 'N/A')
        worst_month = metrics.get('worst_month', 'N/A')
        trades_per_day = metrics.get('trades_per_day_avg', 0)
        
        avg_position_size = metrics.get('avg_position_size_shares', 0)
        sizing_consistency = metrics.get('sizing_consistency_score', 0)
        
        max_drawdown = metrics.get('max_drawdown', 0)
        volatility = metrics.get('daily_pnl_volatility', 0)
        
        # Build comprehensive prompt
        prompt = f"""You are analyzing REAL trading data. Every number below is ACTUAL data from this trader's closed positions. Do NOT invent, estimate, or hallucinate any statistics.

**ACTUAL PERFORMANCE DATA:**
- Cumulative Realized P&L: ${cumulative_pnl:,.2f}
- Total Closed Trades: {total_trades}
- Win Rate: {win_rate:.1f}%
- Profit Factor: {profit_factor:.2f}
- Average Gain: ${avg_gain:.2f}
- Average Loss: ${avg_loss:.2f}

**ACTUAL HOLDING TIME DATA:**
- Average Holding Time: {avg_hold_time:.0f} minutes ({avg_hold_time/60:.1f} hours)
- Winners Held: {avg_hold_winners:.0f} minutes ({avg_hold_winners/60:.1f} hours)
- Losers Held: {avg_hold_losers:.0f} minutes ({avg_hold_losers/60:.1f} hours)
- Quick Flip Rate: {quick_flip_rate*100:.1f}% (trades held < 1 hour)

**ACTUAL SYMBOL CONCENTRATION:**
- Total Unique Symbols Traded: {unique_symbols}
- Top 3 Symbols: {', '.join(top_3_symbols[:3]) if top_3_symbols else 'N/A'}
- Top 3 Concentration: {concentration_ratio*100:.1f}% of all trades
- Leveraged ETF Usage: {leveraged_pct*100:.1f}% of trades

**ACTUAL WIN/LOSS STREAKS:**
- Current Streak: {"+" if current_streak > 0 else ""}{current_streak} trades
- Longest Winning Streak: {longest_win_streak} trades
- Longest Losing Streak: {longest_loss_streak} trades

**ACTUAL TIMING PATTERNS (EST):**
- Best Trading Hour: {best_hour} EST (avg ${best_hour_pnl:.2f}/trade)
- Worst Trading Hour: {worst_hour} EST (avg ${worst_hour_pnl:.2f}/trade)
- Best Month: {best_month}
- Worst Month: {worst_month}
- Best Day of Week: {best_weekday}
- Worst Day of Week: {worst_weekday}
- Average Trades Per Day: {trades_per_day:.1f}
- Note: Regular NYSE hours are 09:30-16:00 EST

**ACTUAL POSITION SIZING:**
- Average Position Size: {avg_position_size:.0f} shares
- Sizing Consistency Score: {sizing_consistency:.2f} (0=inconsistent, 1=very consistent)

**ACTUAL RISK METRICS:**
- Maximum Drawdown: ${max_drawdown:,.2f} (largest loss from peak P&L)
- Daily P&L Volatility: ${volatility:.2f} (standard deviation of daily P&L)
- Best Performing Symbol: {best_symbol}
- Worst Performing Symbol: {worst_symbol}

**STRICT INSTRUCTIONS:**
1. ONLY reference the EXACT numbers provided above - do NOT make up statistics
2. When mentioning hours, note if they fall outside regular NYSE hours (09:30-16:00 EST)
3. Provide 2-3 pattern insights using ONLY the data above
4. Provide 2-3 risk notes with specific thresholds from the data
5. Provide 3-4 actionable recommendations based on the ACTUAL patterns observed

**ABSOLUTE RULES:**
- NO ticker buy/sell recommendations
- NO invented statistics or percentages
- ONLY use numbers explicitly shown above
- If best/worst hour is outside 09:30-16:00 EST, mention this as extended hours trading
- Quote exact metrics in your evidence (e.g., "Your win rate of 55.9%..." not "Your win rate is around 56%")
- Identify ONE biggest strength and ONE biggest weakness from the data"""
        
        return prompt
    
    def _get_fallback_response(self, metrics: Dict[str, Any]) -> AICoachResponse:
        """
        Generate a neutral fallback response when OpenAI is unavailable.
        
        Per PRD: Show neutral fallback on failure.
        """
        logger.info("Generating fallback response")
        
        cumulative_pnl = metrics.get('cumulative_pnl', 0)
        win_rate = metrics.get('win_rate', 0)
        profit_factor = metrics.get('profit_factor', 0)
        
        # Determine performance level
        if cumulative_pnl > 0 and win_rate > 50:
            performance = "positive"
        elif cumulative_pnl < 0:
            performance = "negative"
        else:
            performance = "mixed"
        
        # Build fallback insights
        summary = (
            f"Your trading performance shows {performance} results with a "
            f"{win_rate:.1f}% win rate and ${cumulative_pnl:,.2f} cumulative P&L. "
            f"Continue monitoring your metrics to identify areas for improvement."
        )
        
        pattern_insights = [
            PatternInsight(
                title="Win Rate Analysis",
                evidence_metric=f"Current win rate: {win_rate:.1f}%",
                why_it_matters="Win rate above 50% suggests more winning trades than losing trades, but should be considered alongside profit factor."
            ),
            PatternInsight(
                title="Profit Factor Assessment",
                evidence_metric=f"Profit factor: {profit_factor:.2f}",
                why_it_matters="A profit factor above 1.0 indicates that total gains exceed total losses, which is essential for long-term profitability."
            )
        ]
        
        risk_notes = [
            RiskNote(
                title="Position Sizing Consistency",
                trigger_condition="Large variation in trade sizes can increase risk",
                mitigation_tip="Consider maintaining consistent position sizes relative to account size to manage risk effectively."
            ),
            RiskNote(
                title="Drawdown Monitoring",
                trigger_condition="Extended losing streaks can impact account equity",
                mitigation_tip="Set maximum drawdown limits and review trading strategy if limits are approached."
            )
        ]
        
        top_actions = [
            TopAction(priority=1, action="Review your best and worst performing symbols to identify what's working and what isn't."),
            TopAction(priority=2, action="Analyze your trading patterns by day of week to optimize timing."),
            TopAction(priority=3, action="Maintain a trading journal to document the reasoning behind each trade."),
            TopAction(priority=4, action="Consider setting profit targets and stop losses for each position to manage risk.")
        ]
        
        return AICoachResponse(
            summary=summary,
            pattern_insights=pattern_insights,
            risk_notes=risk_notes,
            top_actions=top_actions
        )
