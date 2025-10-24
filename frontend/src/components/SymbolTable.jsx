import { useState, useMemo } from 'react'
import { motion } from 'framer-motion'
import { Search, ArrowUpDown, Download } from 'lucide-react'

const SymbolTable = ({ data }) => {
  const [searchTerm, setSearchTerm] = useState('')
  const [sortConfig, setSortConfig] = useState({ key: 'total_pnl', direction: 'desc' })

  if (!data || data.length === 0) {
    return (
      <div className="bg-secondary rounded-lg p-8 border border-primary/10">
        <p className="text-center text-text-dark">No symbol data available</p>
      </div>
    )
  }

  // Filter and sort data
  const processedData = useMemo(() => {
    let filtered = data.filter(item =>
      item.symbol.toLowerCase().includes(searchTerm.toLowerCase())
    )

    if (sortConfig.key) {
      filtered.sort((a, b) => {
        const aVal = a[sortConfig.key]
        const bVal = b[sortConfig.key]
        
        if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1
        if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1
        return 0
      })
    }

    return filtered
  }, [data, searchTerm, sortConfig])

  const handleSort = (key) => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc'
    }))
  }

  const exportToCSV = () => {
    const headers = ['Symbol', 'Trades', 'Total P&L', 'Avg Return %']
    const rows = processedData.map(item => [
      item.symbol,
      item.num_trades,
      item.total_pnl,
      item.avg_return_pct
    ])

    const csv = [
      headers.join(','),
      ...rows.map(row => row.join(','))
    ].join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'symbol-breakdown.csv'
    a.click()
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="bg-secondary rounded-lg p-6 border border-primary/10"
    >
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-text">Per-Symbol Breakdown</h2>
        
        <div className="flex items-center space-x-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-text-dark" />
            <input
              type="text"
              placeholder="Search symbols..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 bg-background border border-primary/20 rounded-lg text-sm text-text placeholder-text-dark focus:outline-none focus:border-primary transition-colors"
            />
          </div>

          {/* Export Button */}
          <button
            onClick={exportToCSV}
            className="flex items-center space-x-2 px-4 py-2 bg-primary/10 hover:bg-primary/20 text-primary rounded-lg transition-colors"
          >
            <Download className="w-4 h-4" />
            <span className="text-sm font-medium">Export</span>
          </button>
        </div>
      </div>

      <div className="overflow-x-auto max-h-96 overflow-y-auto">
        <table className="w-full">
          <thead className="sticky top-0 bg-secondary z-10">
            <tr className="border-b border-primary/20">
              <th 
                className="text-left py-3 px-4 text-sm font-semibold text-text-dark cursor-pointer hover:text-primary transition-colors"
                onClick={() => handleSort('symbol')}
              >
                <div className="flex items-center space-x-2">
                  <span>Symbol</span>
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th 
                className="text-right py-3 px-4 text-sm font-semibold text-text-dark cursor-pointer hover:text-primary transition-colors"
                onClick={() => handleSort('num_trades')}
              >
                <div className="flex items-center justify-end space-x-2">
                  <span>Trades</span>
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th 
                className="text-right py-3 px-4 text-sm font-semibold text-text-dark cursor-pointer hover:text-primary transition-colors"
                onClick={() => handleSort('total_pnl')}
              >
                <div className="flex items-center justify-end space-x-2">
                  <span>Total P&L</span>
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th 
                className="text-right py-3 px-4 text-sm font-semibold text-text-dark cursor-pointer hover:text-primary transition-colors"
                onClick={() => handleSort('avg_return_pct')}
              >
                <div className="flex items-center justify-end space-x-2">
                  <span>Avg Return %</span>
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
            </tr>
          </thead>
          <tbody>
            {processedData.map((item, index) => (
              <motion.tr
                key={item.symbol}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
                className="border-b border-primary/10 hover:bg-primary/5 transition-colors"
              >
                <td className="py-3 px-4">
                  <span className="font-mono font-semibold text-primary">{item.symbol}</span>
                </td>
                <td className="py-3 px-4 text-right text-text">{item.num_trades}</td>
                <td className={`py-3 px-4 text-right font-mono font-semibold ${
                  item.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'
                }`}>
                  ${item.total_pnl.toLocaleString()}
                </td>
                <td className={`py-3 px-4 text-right font-mono ${
                  item.avg_return_pct >= 0 ? 'text-green-400' : 'text-red-400'
                }`}>
                  {item.avg_return_pct >= 0 ? '+' : ''}{item.avg_return_pct}%
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>

      {processedData.length === 0 && (
        <div className="text-center py-8 text-text-dark">
          No symbols match your search
        </div>
      )}
    </motion.div>
  )
}

export default SymbolTable
