import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import MetricCard from '../components/MetricCard'
import PnLChart from '../components/PnLChart'
import SymbolTable from '../components/SymbolTable'
import AISuggestions from '../components/AISuggestions'
import { 
  DollarSign, 
  TrendingUp, 
  Target, 
  Award,
  Percent,
  BarChart3,
  AlertTriangle,
  Activity,
  Clock,
  Zap,
  TrendingDown,
  Flame,
  Users
} from 'lucide-react'

const Dashboard = ({ metrics, fileName }) => {
  const navigate = useNavigate()

  useEffect(() => {
    if (!metrics) {
      console.log('No metrics found, redirecting to upload page')
      // Use replace to avoid adding to history
      navigate('/', { replace: true })
    }
  }, [metrics, navigate])

  if (!metrics) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="mb-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          </div>
          <p className="text-text text-lg">No data available</p>
          <p className="text-text-dark mt-2">Redirecting to upload page...</p>
          <button 
            onClick={() => navigate('/')}
            className="mt-4 px-6 py-2 bg-primary text-background rounded-lg hover:bg-primary-light transition-colors"
          >
            Go to Upload Page
          </button>
        </div>
      </div>
    )
  }

  // Debug logging
  console.log('Dashboard metrics:', metrics)
  console.log('Has summary:', !!metrics.summary)
  console.log('Has win_loss:', !!metrics.win_loss)
  console.log('Has per_symbol:', !!metrics.per_symbol)
  console.log('Has pnl_series:', !!metrics.pnl_series)

  // Handle both v1.0 (performance) and v2.0 (summary) backend formats
  const performance = metrics.performance || metrics.summary
  const win_loss = metrics.win_loss || {}
  const risk = metrics.risk || {}
  const efficiency = metrics.efficiency || {}
  const behavioral = metrics.behavioral || {}
  const per_symbol = metrics.per_symbol || []
  const pnl_series = metrics.pnl_series || []
  
  // Check if we have the required data
  if (!performance) {
    console.error('Missing required metrics data:', { performance, win_loss, risk })
    return (
      <div className="container mx-auto px-6 py-8">
        <div className="text-center text-red-400">
          <p>Error: Missing required metrics data</p>
          <pre className="text-xs mt-4">{JSON.stringify(metrics, null, 2)}</pre>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-6 py-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-text mb-2">Trading Dashboard</h1>
            <p className="text-text-dark">
              Analysis of <span className="text-primary font-medium">{fileName}</span>
            </p>
          </div>
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 bg-primary/10 hover:bg-primary/20 text-primary rounded-lg transition-colors font-medium"
          >
            Upload New File
          </button>
        </div>
      </motion.div>

      {/* Main Layout: Metrics on left, AI Suggestions on right */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column - Main Metrics (2/3 width) */}
        <div className="lg:col-span-2 space-y-8">
          {/* Performance Metrics */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-text mb-4 flex items-center">
          <TrendingUp className="w-5 h-5 mr-2 text-primary" />
          Performance Overview
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <MetricCard
            title="Total P&L"
            value={performance.total_pnl}
            icon={DollarSign}
          />
          <MetricCard
            title="Avg Monthly Return"
            value={performance.avg_monthly_return}
            subtitle="Average per month"
            icon={BarChart3}
          />
          <MetricCard
            title="Sharpe Ratio"
            value={performance.sharpe_ratio.toFixed(2)}
            subtitle="Risk-adjusted returns"
            icon={Award}
          />
          <MetricCard
            title="Expectancy"
            value={performance.expectancy}
            subtitle="Expected value per trade"
            icon={Target}
          />
        </div>
      </div>

      {/* Win/Loss Metrics */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-text mb-4 flex items-center">
          <Target className="w-5 h-5 mr-2 text-primary" />
          Win/Loss Analysis
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <MetricCard
            title="Win Rate"
            value={`${win_loss.round_trip_win_rate?.toFixed(1) || win_loss.win_rate.toFixed(1)}%`}
            subtitle={`${win_loss.round_trip_wins || 0}W / ${win_loss.round_trip_losses || 0}L`}
            icon={Percent}
          />
          <MetricCard
            title="Average Win"
            value={win_loss.avg_win}
            icon={TrendingUp}
          />
          <MetricCard
            title="Average Loss"
            value={win_loss.avg_loss}
            icon={AlertTriangle}
            forceColor="red"
          />
          <MetricCard
            title="Profit Factor"
            value={win_loss.profit_factor.toFixed(2)}
            subtitle="Total profit / Total loss"
            icon={BarChart3}
          />
        </div>
      </div>

      {/* Risk Metrics */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-text mb-4 flex items-center">
          <AlertTriangle className="w-5 h-5 mr-2 text-primary" />
          Risk & Exposure
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <MetricCard
            title="Max Drawdown"
            value={`${risk.max_drawdown_pct.toFixed(2)}%`}
            subtitle="Largest peak-to-trough decline"
            icon={AlertTriangle}
          />
          <MetricCard
            title="Avg Hold Length"
            value={`${risk.avg_hold_days.toFixed(1)} days`}
            subtitle="Average position duration"
            icon={Activity}
          />
          <MetricCard
            title="Total Trades"
            value={risk.total_trades.toString()}
            subtitle="Number of positions"
            icon={BarChart3}
          />
        </div>
      </div>

      {/* Trade Efficiency Metrics */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-text mb-4 flex items-center">
          <Zap className="w-5 h-5 mr-2 text-primary" />
          Trade Efficiency
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
          <MetricCard
            title="Avg Hold Time"
            value={`${(efficiency.avg_hold_time_hours / 24).toFixed(1)} days`}
            subtitle={`${efficiency.avg_hold_time_hours?.toFixed(0) || 0} hours`}
            icon={Clock}
          />
          <MetricCard
            title="Avg Trade Size"
            value={efficiency.avg_trade_size || 0}
            subtitle="Capital per position"
            icon={DollarSign}
          />
          <MetricCard
            title="Avg Return/Trade"
            value={`${efficiency.avg_return_per_trade?.toFixed(2) || 0}%`}
            subtitle="Trade efficiency"
            icon={TrendingUp}
          />
          <MetricCard
            title="Return Skewness"
            value={efficiency.return_skewness?.toFixed(2) || 0}
            subtitle={efficiency.return_skewness < 0 ? 'Loss-heavy' : 'Win-heavy'}
            icon={Activity}
          />
          <MetricCard
            title="P&L Volatility"
            value={efficiency.pnl_volatility || 0}
            subtitle="Outcome stability"
            icon={TrendingDown}
          />
        </div>
      </div>

      {/* Behavioral Metrics */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-text mb-4 flex items-center">
          <Flame className="w-5 h-5 mr-2 text-primary" />
          Trading Behavior
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <MetricCard
            title="Win Streak"
            value={behavioral.max_win_streak || 0}
            subtitle={`Max loss: ${behavioral.max_loss_streak || 0}`}
            icon={Flame}
            forceColor="green"
          />
          <MetricCard
            title="Trade Frequency"
            value={`${(behavioral.avg_time_between_trades_hours / 24)?.toFixed(1) || 0} days`}
            subtitle="Avg time between trades"
            icon={Clock}
          />
          <MetricCard
            title="Long/Short Split"
            value={`${behavioral.long_trade_pct?.toFixed(0) || 0}% / ${behavioral.short_trade_pct?.toFixed(0) || 0}%`}
            subtitle="Position bias"
            icon={BarChart3}
          />
          <MetricCard
            title="Diversification"
            value={`${behavioral.unique_symbols || 0} symbols`}
            subtitle={`Top 5: ${behavioral.symbol_concentration_top5?.toFixed(0) || 0}%`}
            icon={Users}
          />
        </div>
      </div>

          {/* P&L Chart */}
          <div>
            <PnLChart data={pnl_series} />
          </div>

          {/* Symbol Breakdown */}
          <div>
            <SymbolTable data={per_symbol} />
          </div>
        </div>

        {/* Right Column - AI Suggestions (1/3 width) */}
        <div className="lg:col-span-1">
          <div className="sticky top-8">
            <AISuggestions metrics={metrics} />
          </div>
        </div>
      </div>

      {/* Footer */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="text-center text-text-dark text-sm py-8 mt-8"
      >
        <p>Jones Software & Data © 2025 - Trading Performance Dashboard</p>
      </motion.div>
    </div>
  )
}

export default Dashboard
