import { useEffect, useRef, useState } from 'react';
import Plot from 'react-plotly.js';
import { motion } from 'framer-motion';
import type { Timeframe } from '../pages/Dashboard';

interface PLChartProps {
  data: Array<{
    date: string;
    cumulative_pnl: number;
  }>;
  benchmarks: string[];
  timeframe: Timeframe;
}

interface BenchmarkData {
  [key: string]: Array<{
    date: string;
    value: number;
  }>;
}

export default function PLChart({ data, benchmarks, timeframe }: PLChartProps) {
  const [benchmarkData, setBenchmarkData] = useState<BenchmarkData>({});
  const prevTimeframe = useRef(timeframe);

  useEffect(() => {
    // Update ref on timeframe change for animation tracking
    prevTimeframe.current = timeframe;
  }, [timeframe]);

  useEffect(() => {
    // Benchmark feature disabled for MVP - will be implemented in future
    // Keeping the state management for when benchmarks are added
    setBenchmarkData({});
  }, [benchmarks, timeframe]);

  // Prepare main P&L trace with color coding
  const dates = data.map((d) => d.date);
  const pnlValues = data.map((d) => d.cumulative_pnl);

  // Split into segments at zero crossings for color coding
  const segments: Array<{
    dates: string[];
    values: number[];
    color: string;
  }> = [];

  let currentSegment: { dates: string[]; values: number[]; color: string } = {
    dates: [],
    values: [],
    color: pnlValues[0] >= 0 ? '#16a34a' : '#dc2626',
  };

  for (let i = 0; i < data.length; i++) {
    const val = pnlValues[i];
    const color = val >= 0 ? '#16a34a' : '#dc2626';

    if (color !== currentSegment.color && currentSegment.dates.length > 0) {
      // Zero crossing detected, finalize current segment
      segments.push({ ...currentSegment });
      currentSegment = {
        dates: [dates[i - 1]], // Include previous point for continuity
        values: [pnlValues[i - 1]],
        color,
      };
    }

    currentSegment.dates.push(dates[i]);
    currentSegment.values.push(val);
  }

  if (currentSegment.dates.length > 0) {
    segments.push(currentSegment);
  }

  // Create traces for each segment
  const plTraces = segments.map((segment) => ({
    x: segment.dates,
    y: segment.values,
    type: 'scatter' as const,
    mode: 'lines' as const,
    name: undefined,
    showlegend: false,
    line: {
      color: segment.color,
      width: 3,
    },
    hovertemplate: '<b>%{x}</b><br>P&L: $%{y:,.2f}<extra></extra>',
  }));

  // Add benchmark traces
  const benchmarkTraces = Object.entries(benchmarkData).map(([symbol, benchData]) => ({
    x: benchData.map((d) => d.date),
    y: benchData.map((d) => d.value),
    type: 'scatter' as const,
    mode: 'lines' as const,
    name: symbol,
    line: {
      color: symbol === 'SPY' ? '#3b82f6' : symbol === 'DIA' ? '#8b5cf6' : '#f59e0b',
      width: 2,
      dash: 'dot' as const,
    },
    hovertemplate: `<b>${symbol}</b><br>%{x}<br>Return: %{y:.2f}%<extra></extra>`,
  }));

  const allTraces = [...plTraces, ...benchmarkTraces];

  return (
    <motion.div
      key={timeframe}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="w-full"
    >
      <Plot
        data={allTraces}
        layout={{
          autosize: true,
          paper_bgcolor: 'rgba(0,0,0,0)',
          plot_bgcolor: 'rgba(0,0,0,0)',
          font: {
            color: '#9ca3af',
            family: 'system-ui, -apple-system, sans-serif',
          },
          xaxis: {
            title: 'Date',
            gridcolor: '#374151',
            showgrid: true,
            zeroline: false,
            color: '#9ca3af',
          },
          yaxis: {
            title: 'Cumulative P&L ($)',
            gridcolor: '#374151',
            showgrid: true,
            zeroline: true,
            zerolinecolor: '#6b7280',
            zerolinewidth: 2,
            color: '#9ca3af',
          },
          hovermode: 'x unified',
          legend: {
            orientation: 'h' as const,
            yanchor: 'bottom',
            y: 1.02,
            xanchor: 'right',
            x: 1,
            bgcolor: 'rgba(31, 41, 55, 0.8)',
            bordercolor: '#4b5563',
            borderwidth: 1,
          },
          margin: {
            l: 60,
            r: 40,
            t: 40,
            b: 60,
          },
          transition: {
            duration: 500,
            easing: 'cubic-in-out' as const,
          },
        }}
        config={{
          responsive: true,
          displayModeBar: false,
          displaylogo: false,
          staticPlot: false,
        }}
        style={{ width: '100%', height: '500px' }}
        useResizeHandler={true}
      />
    </motion.div>
  );
}
