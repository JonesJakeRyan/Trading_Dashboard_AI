import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import TypedText from '../animations/TypedText';
import type { Timeframe } from '../pages/Dashboard';

interface AICoachPanelProps {
  jobId: string | null;
  isDemo: boolean;
  timeframe: Timeframe;
}

interface AIInsight {
  summary: string;
  pattern_insights: Array<{
    title: string;
    evidence_metric: string;
    why_it_matters: string;
  }>;
  risk_notes: Array<{
    title: string;
    trigger_condition: string;
    mitigation_tip: string;
  }>;
  top_actions: Array<{
    priority: number;
    action: string;
  }>;
}

export default function AICoachPanel({ jobId, isDemo, timeframe }: AICoachPanelProps) {
  const [insights, setInsights] = useState<AIInsight | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showContent, setShowContent] = useState(false);

  useEffect(() => {
    fetchInsights();
  }, [jobId, isDemo, timeframe]);

  const fetchInsights = async () => {
    setLoading(true);
    setError(null);
    setShowContent(false);

    try {
      const endpoint = isDemo ? '/api/demo/ai/coach' : '/api/v1/ai/coach';
      const params = new URLSearchParams({ timeframe });
      if (jobId && !isDemo) params.append('job_id', jobId);

      const response = await fetch(`${endpoint}?${params}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch AI insights');
      }

      const data = await response.json();
      setInsights(data);
      
      // Delay showing content to allow for typing animation
      setTimeout(() => setShowContent(true), 300);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load insights');
      setInsights(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.4 }}
      className="bg-gray-800 rounded-lg p-6 shadow-xl border border-gray-700"
    >
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
          <svg
            className="w-6 h-6 text-white"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
            />
          </svg>
        </div>
        <div>
          <h2 className="text-2xl font-semibold">AI Coach Insights</h2>
          <p className="text-sm text-gray-400">Pattern analysis and risk observations</p>
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
        </div>
      )}

      {error && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="p-4 bg-red-900/50 border border-red-700 rounded-lg text-red-200"
        >
          {error}
        </motion.div>
      )}

      <AnimatePresence mode="wait">
        {showContent && insights && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
          >
            {/* Summary */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-2 text-purple-400">Summary</h3>
              <TypedText
                text={insights.summary}
                speed={20}
                className="text-gray-300 leading-relaxed"
              />
            </div>

            {/* Pattern Insights */}
            {insights.pattern_insights.length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-3 text-green-400">Pattern Insights</h3>
                <div className="space-y-3">
                  {insights.pattern_insights.map((insight, idx) => (
                    <motion.div
                      key={idx}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.4, delay: idx * 0.1 }}
                      className="p-4 bg-gray-700/50 rounded-lg border border-gray-600"
                    >
                      <h4 className="font-semibold mb-1 text-white">{insight.title}</h4>
                      <p className="text-sm text-gray-400 mb-2">
                        <strong>Evidence:</strong> {insight.evidence_metric}
                      </p>
                      <p className="text-sm text-gray-300">
                        <strong>Why it matters:</strong> {insight.why_it_matters}
                      </p>
                    </motion.div>
                  ))}
                </div>
              </div>
            )}

            {/* Risk Notes */}
            {insights.risk_notes.length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-3 text-yellow-400">Risk Notes</h3>
                <div className="space-y-3">
                  {insights.risk_notes.map((risk, idx) => (
                    <motion.div
                      key={idx}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.4, delay: idx * 0.1 + 0.2 }}
                      className="p-4 bg-yellow-900/20 rounded-lg border border-yellow-700/50"
                    >
                      <h4 className="font-semibold mb-1 text-yellow-300">{risk.title}</h4>
                      <p className="text-sm text-gray-400 mb-2">
                        <strong>Trigger:</strong> {risk.trigger_condition}
                      </p>
                      <p className="text-sm text-gray-300">
                        <strong>Mitigation:</strong> {risk.mitigation_tip}
                      </p>
                    </motion.div>
                  ))}
                </div>
              </div>
            )}

            {/* Top Actions */}
            {insights.top_actions.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold mb-3 text-blue-400">Recommended Actions</h3>
                <div className="space-y-2">
                  {insights.top_actions
                    .sort((a, b) => a.priority - b.priority)
                    .map((action, idx) => (
                      <motion.div
                        key={idx}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.4, delay: idx * 0.1 + 0.4 }}
                        className="flex items-start gap-3 p-3 bg-blue-900/20 rounded-lg border border-blue-700/50"
                      >
                        <span className="flex-shrink-0 w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center text-sm font-bold">
                          {action.priority}
                        </span>
                        <p className="text-sm text-gray-300 pt-0.5">{action.action}</p>
                      </motion.div>
                    ))}
                </div>
              </div>
            )}

            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 1 }}
              className="mt-6 pt-4 border-t border-gray-700 text-xs text-gray-500"
            >
              <p>
                ⚠️ These insights are for educational purposes only and do not constitute financial advice.
                No specific ticker recommendations are provided.
              </p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
