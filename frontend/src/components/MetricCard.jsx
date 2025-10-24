import { motion } from 'framer-motion'

const MetricCard = ({ title, value, subtitle, icon: Icon, trend, forceColor }) => {
  const isPositive = forceColor === 'green' ? true : 
                     forceColor === 'red' ? false :
                     trend === 'up' || (typeof value === 'number' && value > 0) || 
                     (typeof value === 'string' && value.includes('-') === false && parseFloat(value) > 0)

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="bg-secondary rounded-lg p-6 border border-primary/10 hover:border-primary/30 transition-all"
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          {Icon && (
            <div className="bg-primary/10 p-2 rounded-lg">
              <Icon className="w-5 h-5 text-primary" />
            </div>
          )}
          <h3 className="text-sm font-medium text-text-dark">{title}</h3>
        </div>
      </div>
      
      <div className="space-y-1">
        <p className={`text-3xl font-bold font-mono ${
          isPositive ? 'text-green-400' : 'text-red-400'
        }`}>
          {typeof value === 'number' ? 
            (value >= 0 ? `$${value.toLocaleString()}` : `-$${Math.abs(value).toLocaleString()}`) 
            : value
          }
        </p>
        {subtitle && (
          <p className="text-xs text-text-dark">{subtitle}</p>
        )}
      </div>
    </motion.div>
  )
}

export default MetricCard
