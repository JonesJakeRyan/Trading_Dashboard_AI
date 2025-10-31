import { useState, useEffect } from 'react';
import { motion, useMotionValue, animate } from 'framer-motion';

interface MetricsHeaderProps {
  metrics: {
    cumulative_pnl: number;
    total_trades: number;
    win_rate: number;
    avg_gain: number;
    avg_loss: number;
    profit_factor: number;
    best_symbol: string;
    worst_symbol: string;
    best_weekday: string;
    worst_weekday: string;
  };
}

interface MetricCardProps {
  label: string;
  value: number | string;
  format?: 'currency' | 'percentage' | 'number' | 'decimal' | 'text';
  delay?: number;
  colorize?: boolean;
}

function MetricCard({ label, value, format = 'number', delay = 0, colorize = false }: MetricCardProps) {
  const motionValue = useMotionValue(0);
  const [displayText, setDisplayText] = useState<string>('');

  useEffect(() => {
    if (format === 'text' || typeof value === 'string') {
      setDisplayText(value?.toString() || 'N/A');
      return;
    }

    const numValue = typeof value === 'number' ? value : (value ? parseFloat(value as string) : 0);
    
    const controls = animate(motionValue, numValue, {
      duration: 1.5,
      delay,
      ease: 'easeOut',
      onUpdate: (latest) => {
        if (format === 'currency') {
          setDisplayText(`$${latest.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}`);
        } else if (format === 'percentage') {
          setDisplayText(`${Math.round(latest)}%`);
        } else if (format === 'decimal') {
          setDisplayText(latest.toFixed(2));
        } else {
          setDisplayText(Math.round(latest).toString());
        }
      },
    });
    
    return controls.stop;
  }, [value, format, delay, motionValue]);

  const getColorClass = () => {
    if (!colorize || typeof value !== 'number') return 'text-white';
    return value >= 0 ? 'text-profit' : 'text-loss';
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
      className="bg-gray-800 rounded-lg p-6 border border-gray-700 shadow-lg"
    >
      <p className="text-gray-400 text-sm mb-2">{label}</p>
      <p className={`text-3xl font-bold ${getColorClass()}`}>
        {displayText || (format === 'text' ? value : '0')}
      </p>
    </motion.div>
  );
}

export default function MetricsHeader({ metrics }: MetricsHeaderProps) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5, delay: 0.2 }}
      className="mb-8"
    >
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
        <MetricCard
          label="Cumulative Realized P&L"
          value={metrics.cumulative_pnl}
          format="currency"
          delay={0.1}
          colorize
        />
        <MetricCard
          label="Total Trades"
          value={metrics.total_trades}
          format="number"
          delay={0.15}
        />
        <MetricCard
          label="Win Rate"
          value={metrics.win_rate * 100}
          format="percentage"
          delay={0.2}
        />
        <MetricCard
          label="Profit Factor"
          value={metrics.profit_factor}
          format="decimal"
          delay={0.25}
          colorize
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Avg Gain"
          value={metrics.avg_gain}
          format="currency"
          delay={0.3}
          colorize
        />
        <MetricCard
          label="Avg Loss"
          value={metrics.avg_loss}
          format="currency"
          delay={0.35}
          colorize
        />
        <MetricCard
          label="Best Symbol"
          value={metrics.best_symbol}
          format="text"
          delay={0.4}
        />
        <MetricCard
          label="Worst Symbol"
          value={metrics.worst_symbol}
          format="text"
          delay={0.45}
        />
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.5 }}
        className="mt-4 p-4 bg-blue-900/20 border border-blue-700/50 rounded-lg"
      >
        <p className="text-sm text-blue-200">
          <strong>Assumptions:</strong> FIFO matching • Realized P&L only • USD equities/ETFs • 
          No fees, dividends, or corporate actions • Calendar days (EST)
        </p>
      </motion.div>
    </motion.div>
  );
}
