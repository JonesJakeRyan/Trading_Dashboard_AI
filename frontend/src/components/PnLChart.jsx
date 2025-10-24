import { useState, useMemo } from 'react'
import { ComposedChart, Line, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import { motion } from 'framer-motion'
import { Calendar, TrendingUp } from 'lucide-react'

const PnLChart = ({ data }) => {
  const [timeframe, setTimeframe] = useState('all')
  const [chartType, setChartType] = useState('cumulative')

  // Debug: log the data
  console.log('PnLChart received data:', data)
  console.log('Data length:', data?.length)
  console.log('First few items:', data?.slice(0, 5))

  if (!data || data.length === 0) {
    return (
      <div className="bg-secondary rounded-lg p-8 border border-primary/10">
        <p className="text-center text-text-dark">No data available</p>
      </div>
    )
  }

  // Filter data based on timeframe - use useMemo to recalculate when timeframe changes
  const chartData = useMemo(() => {
    if (!data || data.length === 0) {
      console.log('No data available for chart')
      return []
    }

    let filtered = [...data]

    // Apply timeframe filter
    if (timeframe !== 'all') {
      const now = new Date()
      const cutoffDate = new Date()
      
      switch (timeframe) {
        case 'week':
          cutoffDate.setDate(now.getDate() - 7)
          break
        case 'month':
          cutoffDate.setMonth(now.getMonth() - 1)
          break
        case 'ytd':
          cutoffDate.setMonth(0)
          cutoffDate.setDate(1)
          break
        default:
          break
      }

      filtered = filtered.filter(item => new Date(item.date) >= cutoffDate)
    }

    console.log('Filtered chart data:', filtered)
    return filtered
  }, [data, timeframe, chartType])

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className="bg-secondary border border-primary/20 rounded-lg p-3 shadow-lg">
          <p className="text-xs text-text-dark mb-1">{data.date}</p>
          <p className="text-sm font-bold text-primary">
            {chartType === 'cumulative' 
              ? `$${data.cumulative_pnl?.toLocaleString() || 0}`
              : `$${data.daily_pnl?.toLocaleString() || 0}`
            }
          </p>
        </div>
      )
    }
    return null
  }

  const timeframeButtons = [
    { label: '1W', value: 'week' },
    { label: '1M', value: 'month' },
    { label: 'YTD', value: 'ytd' },
    { label: 'All', value: 'all' },
  ]

  const chartTypeButtons = [
    { label: 'Cumulative P&L', value: 'cumulative' },
    { label: 'Daily Returns', value: 'daily' },
  ]

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="bg-secondary rounded-lg p-6 border border-primary/10"
    >
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="bg-primary/10 p-2 rounded-lg">
            <TrendingUp className="w-5 h-5 text-primary" />
          </div>
          <h2 className="text-xl font-bold text-text">Performance Chart</h2>
        </div>

        <div className="flex items-center space-x-4">
          {/* Chart Type Selector */}
          <div className="flex space-x-2">
            {chartTypeButtons.map((btn) => (
              <button
                key={btn.value}
                onClick={() => setChartType(btn.value)}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
                  chartType === btn.value
                    ? 'bg-primary text-background'
                    : 'bg-background text-text hover:bg-primary/10'
                }`}
              >
                {btn.label}
              </button>
            ))}
          </div>

          {/* Timeframe Selector */}
          <div className="flex items-center space-x-2">
            <Calendar className="w-4 h-4 text-text-dark" />
            {timeframeButtons.map((btn) => (
              <button
                key={btn.value}
                onClick={() => setTimeframe(btn.value)}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
                  timeframe === btn.value
                    ? 'bg-primary text-background'
                    : 'bg-background text-text hover:bg-primary/10'
                }`}
              >
                {btn.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={400}>
        <ComposedChart data={chartData}>
          <defs>
            <linearGradient id="colorPnLGreen" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10b981" stopOpacity={0.2}/>
              <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
            </linearGradient>
            <linearGradient id="colorPnLRed" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ef4444" stopOpacity={0.2}/>
              <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1F2833" />
          <XAxis 
            dataKey="date" 
            stroke="#8B8C8D"
            style={{ fontSize: '12px' }}
            tickFormatter={(value) => {
              const date = new Date(value)
              return `${date.getMonth() + 1}/${date.getDate()}`
            }}
          />
          <YAxis 
            stroke="#8B8C8D"
            style={{ fontSize: '12px' }}
            tickFormatter={(value) => `$${value.toLocaleString()}`}
          />
          <Tooltip content={<CustomTooltip />} />
          
          {/* Reference line at 0 */}
          <ReferenceLine 
            y={0} 
            stroke="#8B8C8D" 
            strokeDasharray="3 3"
            strokeWidth={2}
            label={{ value: 'Break Even', fill: '#8B8C8D', fontSize: 12 }}
          />
          
          {/* Single line that changes color based on value */}
          <Line
            type="monotone"
            dataKey={chartType === 'cumulative' ? 'cumulative_pnl' : 'daily_pnl'}
            stroke="#FFD700"
            strokeWidth={2.5}
            dot={false}
            isAnimationActive={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </motion.div>
  )
}

export default PnLChart
