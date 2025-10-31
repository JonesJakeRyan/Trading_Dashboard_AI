import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import MetricsHeader from '../components/MetricsHeader';
import TimeframeSelector from '../components/TimeframeSelector';
import PLChart from '../charts/PLChart';
import AICoachPanel from '../components/AICoachPanel';
import config from '../config';

export type Timeframe = 'ALL' | 'YTD' | '6M' | '3M' | '1M' | '1W';

interface DashboardData {
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
  chart_data: Array<{
    date: string;
    cumulative_pnl: number;
  }>;
}

export default function Dashboard() {
  const [searchParams] = useSearchParams();
  const jobId = searchParams.get('job_id');
  const isDemo = searchParams.get('demo') === 'true';

  const [timeframe, setTimeframe] = useState<Timeframe>('ALL');
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // const [benchmarksEnabled, setBenchmarksEnabled] = useState<string[]>([]); // Reserved for future benchmark feature

  useEffect(() => {
    fetchDashboardData();
  }, [timeframe, jobId, isDemo]);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);

    try {
      const apiBase = config.apiUrl || '';
      const metricsEndpoint = isDemo ? `${apiBase}/api/demo/metrics` : `${apiBase}/api/v1/metrics`;
      const chartEndpoint = isDemo ? `${apiBase}/api/demo/chart` : `${apiBase}/api/v1/chart`;
      const params = new URLSearchParams({ timeframe });
      if (jobId && !isDemo) params.append('job_id', jobId);

      // Fetch metrics and chart data in parallel
      const [metricsResponse, chartResponse] = await Promise.all([
        fetch(`${metricsEndpoint}?${params}`),
        fetch(`${chartEndpoint}?${params}`)
      ]);

      if (!metricsResponse.ok || !chartResponse.ok) {
        const errorText = await metricsResponse.text();
        console.error('API Error:', { 
          status: metricsResponse.status, 
          url: metricsEndpoint,
          response: errorText.substring(0, 200)
        });
        throw new Error(`Failed to fetch dashboard data: ${metricsResponse.status}`);
      }

      const metricsResult = await metricsResponse.json();
      const chartResult = await chartResponse.json();

      // Combine results
      setData({
        metrics: metricsResult.metrics || metricsResult,
        chart_data: chartResult.data || []
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  // Benchmark toggle function - reserved for future use
  // const toggleBenchmark = (symbol: string) => {
  //   setBenchmarksEnabled((prev) =>
  //     prev.includes(symbol)
  //       ? prev.filter((s) => s !== symbol)
  //       : [...prev, symbol]
  //   );
  // };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center"
        >
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading dashboard...</p>
        </motion.div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-red-900/50 border border-red-700 rounded-lg p-8 max-w-md"
        >
          <h2 className="text-2xl font-bold mb-4">Error</h2>
          <p className="text-red-200">{error || 'Failed to load dashboard'}</p>
        </motion.div>
      </div>
    );
  }

  // Empty state: no trades found
  if (data.metrics.total_trades === 0 || data.chart_data.length === 0) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gray-800 border border-gray-700 rounded-lg p-8 max-w-md text-center"
        >
          <div className="text-6xl mb-4">📊</div>
          <h2 className="text-2xl font-bold mb-4">No Trades Found</h2>
          <p className="text-gray-400 mb-6">
            No closed trades were found in your uploaded data. Please ensure your CSV contains completed trades with both buy and sell executions.
          </p>
          <a
            href="/"
            className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-6 rounded-lg transition-colors"
          >
            Upload New CSV
          </a>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-8"
        >
          <h1 className="text-4xl font-bold mb-2">Trading Dashboard</h1>
          <p className="text-gray-400">
            Cumulative Realized P&L • FIFO Matching • USD Only
          </p>
        </motion.div>

        {/* Timeframe Selector */}
        <TimeframeSelector
          selected={timeframe}
          onChange={setTimeframe}
        />

        {/* Metrics Header */}
        <MetricsHeader metrics={data.metrics} />

        {/* Chart Section */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="bg-gray-800 rounded-lg p-6 shadow-xl border border-gray-700 mb-8"
          aria-label="Cumulative profit and loss chart"
        >
          <div className="mb-4">
            <h2 className="text-2xl font-semibold">Cumulative P&L</h2>
            {/* Benchmark buttons hidden for MVP - will be enabled in future release */}
          </div>
          <PLChart
            data={data.chart_data}
            benchmarks={[]} // Benchmarks feature reserved for future implementation
            timeframe={timeframe}
          />
        </motion.section>

        {/* AI Coach Panel */}
        <AICoachPanel
          jobId={jobId}
          isDemo={isDemo}
          timeframe={timeframe}
        />
      </div>
    </div>
  );
}
