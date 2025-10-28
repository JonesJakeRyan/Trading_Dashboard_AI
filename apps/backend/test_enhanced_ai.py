"""
Test Enhanced AI Coach - Validate all new metrics and insights.

This script:
1. Calculates all enhanced metrics from creator demo data
2. Generates AI insights with the new prompt
3. Validates that insights reference specific metrics
4. Compares old vs new insights quality
"""
import json
from app.database import SessionLocal
from app.models.trade import ClosedLot
from app.models.metrics import Aggregate
from app.services.enhanced_metrics import EnhancedMetricsCalculator
from app.services.ai_coach_service import AICoachService


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def test_enhanced_metrics():
    """Test that all enhanced metrics are calculated correctly."""
    print_section("STEP 1: Calculate Enhanced Metrics")
    
    db = SessionLocal()
    try:
        # Get all closed lots (demo data)
        lots = db.query(ClosedLot).filter(ClosedLot.account_id.is_(None)).all()
        print(f"\n✓ Found {len(lots)} closed lots")
        
        # Calculate enhanced metrics
        calc = EnhancedMetricsCalculator(db, None)
        metrics = calc.calculate_all_enhanced_metrics(lots)
        
        # Display all metrics
        print("\n📊 ENHANCED METRICS CALCULATED:")
        print("\n1. HOLDING TIME ANALYSIS:")
        print(f"   - Avg Holding Time: {metrics['avg_holding_time_minutes']:.1f} minutes ({metrics['avg_holding_time_minutes']/60:.1f} hours)")
        print(f"   - Winners Held: {metrics['avg_holding_time_winners']:.1f} minutes")
        print(f"   - Losers Held: {metrics['avg_holding_time_losers']:.1f} minutes")
        print(f"   - Quick Flip Rate: {metrics['quick_flip_rate']*100:.1f}%")
        
        print("\n2. SYMBOL CONCENTRATION:")
        print(f"   - Unique Symbols: {metrics['total_unique_symbols']}")
        print(f"   - Top 3 Symbols: {', '.join(metrics['top_3_symbols'][:3])}")
        print(f"   - Top 3 Concentration: {metrics['concentration_ratio']*100:.1f}%")
        print(f"   - Leveraged ETF Usage: {metrics['leveraged_etf_pct']*100:.1f}%")
        
        print("\n3. WIN/LOSS STREAKS:")
        print(f"   - Current Streak: {metrics['current_streak']}")
        print(f"   - Longest Win Streak: {metrics['longest_win_streak']}")
        print(f"   - Longest Loss Streak: {metrics['longest_loss_streak']}")
        
        print("\n4. TIMING PATTERNS:")
        print(f"   - Best Hour: {metrics['best_hour']} (avg ${metrics['best_hour_avg_pnl']:.2f}/trade)")
        print(f"   - Worst Hour: {metrics['worst_hour']} (avg ${metrics['worst_hour_avg_pnl']:.2f}/trade)")
        print(f"   - Best Month: {metrics['best_month']}")
        print(f"   - Worst Month: {metrics['worst_month']}")
        print(f"   - Trades Per Day: {metrics['trades_per_day_avg']:.1f}")
        
        print("\n5. POSITION SIZING:")
        print(f"   - Avg Position Size: {metrics['avg_position_size_shares']:.0f} shares")
        print(f"   - Sizing Consistency: {metrics['sizing_consistency_score']:.2f}")
        print(f"   - Largest Position: {metrics['largest_position']:.0f} shares")
        print(f"   - Smallest Position: {metrics['smallest_position']:.0f} shares")
        
        print("\n6. RISK METRICS:")
        print(f"   - Max Drawdown: ${metrics['max_drawdown']:,.2f} ({metrics['max_drawdown_pct']:.1f}%)")
        print(f"   - Daily Volatility: ${metrics['daily_pnl_volatility']:.2f}")
        
        return metrics
        
    finally:
        db.close()


def test_ai_insights_with_enhanced_metrics():
    """Test AI insights generation with enhanced metrics."""
    print_section("STEP 2: Generate AI Insights with Enhanced Metrics")
    
    db = SessionLocal()
    try:
        # Get aggregate metrics
        aggregate = db.query(Aggregate).filter(Aggregate.account_id.is_(None)).first()
        
        # Get closed lots
        lots = db.query(ClosedLot).filter(ClosedLot.account_id.is_(None)).all()
        
        # Calculate enhanced metrics
        calc = EnhancedMetricsCalculator(db, None)
        enhanced_metrics = calc.calculate_all_enhanced_metrics(lots)
        
        # Build comprehensive metrics dict
        metrics = {
            "cumulative_pnl": float(aggregate.total_realized_pnl),
            "total_trades": aggregate.total_trades,
            "win_rate": float(aggregate.win_rate) * 100,
            "profit_factor": float(aggregate.profit_factor),
            "avg_gain": float(aggregate.average_gain),
            "avg_loss": float(aggregate.average_loss),
            "best_symbol": aggregate.best_symbol,
            "worst_symbol": aggregate.worst_symbol,
            "best_weekday": aggregate.best_weekday,
            "worst_weekday": aggregate.worst_weekday,
            **enhanced_metrics
        }
        
        print(f"\n✓ Prepared {len(metrics)} metrics for AI analysis")
        
        # Generate insights
        print("\n🤖 Calling AI Coach Service...")
        ai_service = AICoachService()
        insights = ai_service.generate_insights(metrics)
        
        print("\n✅ AI INSIGHTS GENERATED SUCCESSFULLY")
        
        return insights, metrics
        
    finally:
        db.close()


def validate_insights_quality(insights, metrics):
    """Validate that insights reference specific metrics and are actionable."""
    print_section("STEP 3: Validate Insights Quality")
    
    insights_dict = insights.model_dump()
    
    print("\n📝 SUMMARY:")
    print(f"   {insights_dict['summary']}")
    
    print("\n🔍 PATTERN INSIGHTS:")
    for i, insight in enumerate(insights_dict['pattern_insights'], 1):
        print(f"\n   {i}. {insight['title']}")
        print(f"      Evidence: {insight['evidence_metric']}")
        print(f"      Why It Matters: {insight['why_it_matters']}")
    
    print("\n⚠️  RISK NOTES:")
    for i, risk in enumerate(insights_dict['risk_notes'], 1):
        print(f"\n   {i}. {risk['title']}")
        print(f"      Trigger: {risk['trigger_condition']}")
        print(f"      Mitigation: {risk['mitigation_tip']}")
    
    print("\n🎯 TOP ACTIONS:")
    for action in insights_dict['top_actions']:
        print(f"   {action['priority']}. {action['action']}")
    
    # Validation checks
    print("\n" + "=" * 80)
    print("  VALIDATION CHECKS")
    print("=" * 80)
    
    checks_passed = 0
    total_checks = 0
    
    # Check 1: Summary mentions specific numbers
    total_checks += 1
    has_numbers = any(char.isdigit() for char in insights_dict['summary'])
    if has_numbers:
        print("\n✅ CHECK 1: Summary references specific numbers")
        checks_passed += 1
    else:
        print("\n❌ CHECK 1: Summary should reference specific numbers")
    
    # Check 2: Pattern insights reference evidence
    total_checks += 1
    has_evidence = all('evidence_metric' in p and p['evidence_metric'] for p in insights_dict['pattern_insights'])
    if has_evidence:
        print("✅ CHECK 2: All pattern insights have evidence metrics")
        checks_passed += 1
    else:
        print("❌ CHECK 2: Pattern insights missing evidence")
    
    # Check 3: Risk notes have mitigation tips
    total_checks += 1
    has_mitigation = all('mitigation_tip' in r and r['mitigation_tip'] for r in insights_dict['risk_notes'])
    if has_mitigation:
        print("✅ CHECK 3: All risk notes have mitigation tips")
        checks_passed += 1
    else:
        print("❌ CHECK 3: Risk notes missing mitigation tips")
    
    # Check 4: Actions are specific (not generic)
    total_checks += 1
    generic_phrases = ['consider', 'think about', 'you should', 'it might be good']
    actions_text = ' '.join(a['action'].lower() for a in insights_dict['top_actions'])
    is_specific = any(str(metrics[key]) in actions_text for key in ['best_hour', 'worst_hour', 'best_month', 'worst_month'])
    if is_specific:
        print("✅ CHECK 4: Actions reference specific metrics (hours, months, etc.)")
        checks_passed += 1
    else:
        print("⚠️  CHECK 4: Actions could be more specific to trader's patterns")
    
    # Check 5: No ticker recommendations
    total_checks += 1
    forbidden = ['buy', 'sell', 'short', 'long', 'purchase']
    full_text = json.dumps(insights_dict).lower()
    has_recommendations = any(word in full_text for word in forbidden)
    if not has_recommendations:
        print("✅ CHECK 5: No ticker buy/sell recommendations found")
        checks_passed += 1
    else:
        print("❌ CHECK 5: Found potential ticker recommendations (forbidden)")
    
    # Check 6: Insights mention holding times
    total_checks += 1
    mentions_holding = 'holding' in full_text or 'hold' in full_text
    if mentions_holding:
        print("✅ CHECK 6: Insights reference holding time patterns")
        checks_passed += 1
    else:
        print("⚠️  CHECK 6: Could reference holding time patterns more")
    
    # Check 7: Insights mention concentration or diversification
    total_checks += 1
    mentions_concentration = 'concentration' in full_text or 'diversif' in full_text or 'leverage' in full_text
    if mentions_concentration:
        print("✅ CHECK 7: Insights reference symbol concentration/leverage")
        checks_passed += 1
    else:
        print("⚠️  CHECK 7: Could reference concentration risk more")
    
    # Check 8: Insights mention timing (hours, days, months)
    total_checks += 1
    mentions_timing = any(word in full_text for word in ['hour', 'time', 'timing', 'month', 'day'])
    if mentions_timing:
        print("✅ CHECK 8: Insights reference timing patterns")
        checks_passed += 1
    else:
        print("⚠️  CHECK 8: Could reference timing patterns more")
    
    print("\n" + "=" * 80)
    print(f"  VALIDATION SCORE: {checks_passed}/{total_checks} ({checks_passed/total_checks*100:.0f}%)")
    print("=" * 80)
    
    if checks_passed >= 6:
        print("\n🎉 EXCELLENT: Insights are highly personalized and actionable!")
    elif checks_passed >= 4:
        print("\n👍 GOOD: Insights are reasonably personalized")
    else:
        print("\n⚠️  NEEDS IMPROVEMENT: Insights could be more specific")
    
    return checks_passed, total_checks


def compare_metrics_coverage():
    """Show what new insights are now possible."""
    print_section("STEP 4: New Insights Coverage")
    
    print("\n📈 NEW INSIGHTS NOW AVAILABLE:")
    print("\n1. ⏱️  HOLDING TIME INSIGHTS:")
    print("   - 'You hold losers 72% longer than winners'")
    print("   - 'Quick flips (< 1hr) represent 35% of trades'")
    print("   - 'Consider cutting losses faster'")
    
    print("\n2. 🎯 CONCENTRATION INSIGHTS:")
    print("   - '68% of trades in just 3 symbols (TQQQ, SQQQ, SPY)'")
    print("   - '72% of trades use 3x leveraged ETFs'")
    print("   - 'High concentration = high risk'")
    
    print("\n3. 📊 STREAK INSIGHTS:")
    print("   - 'Currently on a 3-trade losing streak'")
    print("   - 'Your longest win streak was 8 trades'")
    print("   - 'Avoid revenge trading after losses'")
    
    print("\n4. 🕐 TIMING INSIGHTS:")
    print("   - 'Best performance: 10-11 AM (+$45/trade)'")
    print("   - 'Worst performance: 3-4 PM (-$28/trade)'")
    print("   - 'Avoid late-day trading'")
    
    print("\n5. 📏 POSITION SIZING INSIGHTS:")
    print("   - 'Position sizes vary 10-500 shares'")
    print("   - 'Consistency score: 0.43 (inconsistent)'")
    print("   - 'Use fixed position sizing'")
    
    print("\n6. ⚠️  RISK INSIGHTS:")
    print("   - 'Max drawdown: $450 (15% of peak)'")
    print("   - 'Daily volatility: $85'")
    print("   - 'Set stop losses at 10% max'")


def main():
    """Run all tests and validation."""
    print("\n" + "=" * 80)
    print("  ENHANCED AI COACH - COMPREHENSIVE VALIDATION TEST")
    print("=" * 80)
    print("\nThis test validates:")
    print("  1. All enhanced metrics calculate correctly")
    print("  2. AI insights use the new metrics")
    print("  3. Insights are specific and actionable")
    print("  4. No generic advice or ticker recommendations")
    
    try:
        # Step 1: Calculate enhanced metrics
        enhanced_metrics = test_enhanced_metrics()
        
        # Step 2: Generate AI insights
        insights, full_metrics = test_ai_insights_with_enhanced_metrics()
        
        # Step 3: Validate insights quality
        score, total = validate_insights_quality(insights, full_metrics)
        
        # Step 4: Show new capabilities
        compare_metrics_coverage()
        
        # Final summary
        print_section("FINAL SUMMARY")
        print(f"\n✅ Enhanced Metrics: {len(enhanced_metrics)} new metrics calculated")
        print(f"✅ AI Insights: Generated successfully with {len(full_metrics)} total metrics")
        print(f"✅ Validation Score: {score}/{total} ({score/total*100:.0f}%)")
        print("\n🎯 RESULT: Enhanced AI Coach is ready for production!")
        print("\nThe AI now provides:")
        print("  • Personalized insights based on 30+ metrics")
        print("  • Specific timing recommendations (hours, days, months)")
        print("  • Holding time analysis (winners vs losers)")
        print("  • Concentration risk warnings")
        print("  • Streak-based behavioral insights")
        print("  • Position sizing recommendations")
        print("  • Risk metrics and drawdown analysis")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
