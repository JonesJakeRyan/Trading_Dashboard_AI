import { motion } from 'framer-motion';
import type { Timeframe } from '../pages/Dashboard';

interface TimeframeSelectorProps {
  selected: Timeframe;
  onChange: (timeframe: Timeframe) => void;
}

const timeframes: Timeframe[] = ['ALL', 'YTD', '6M', '3M', '1M', '1W'];

const timeframeLabels: Record<Timeframe, string> = {
  ALL: 'All Time',
  YTD: 'Year to Date',
  '6M': '6 Months',
  '3M': '3 Months',
  '1M': '1 Month',
  '1W': '1 Week',
};

export default function TimeframeSelector({ selected, onChange }: TimeframeSelectorProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.1 }}
      className="mb-8"
      role="group"
      aria-label="Timeframe selection"
    >
      <div className="flex flex-wrap gap-2">
        {timeframes.map((tf) => (
          <button
            key={tf}
            onClick={() => onChange(tf)}
            aria-pressed={selected === tf}
            aria-label={`View ${timeframeLabels[tf]} data`}
            className={`relative px-6 py-2 rounded-lg font-medium transition-all duration-200 ${
              selected === tf
                ? 'bg-blue-600 text-white shadow-lg'
                : 'bg-gray-800 text-gray-300 hover:bg-gray-700 border border-gray-700'
            }`}
          >
            {selected === tf && (
              <motion.div
                layoutId="timeframe-indicator"
                className="absolute inset-0 bg-blue-600 rounded-lg"
                style={{ zIndex: -1 }}
                transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              />
            )}
            <span className="relative z-10">{timeframeLabels[tf]}</span>
          </button>
        ))}
      </div>
    </motion.div>
  );
}
