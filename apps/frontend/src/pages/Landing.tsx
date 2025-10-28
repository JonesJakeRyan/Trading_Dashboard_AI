import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';

type BrokerTemplate = 'webull_v1' | 'robinhood_v1' | 'unified_v1';

export default function Landing() {
  const navigate = useNavigate();
  const [selectedTemplate, setSelectedTemplate] = useState<BrokerTemplate>('unified_v1');
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file');
      return;
    }

    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('template_id', selectedTemplate);

    try {
      const response = await fetch('/api/ingest', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }

      const data = await response.json();
      // Navigate to dashboard with job_id
      navigate(`/dashboard?job_id=${data.job_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleViewDemo = () => {
    navigate('/dashboard?demo=true');
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="max-w-2xl w-full"
      >
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-green-400 to-blue-500 bg-clip-text text-transparent">
            Trading Dashboard
          </h1>
          <p className="text-gray-400 text-lg">
            Upload your trades and visualize your cumulative realized P&L
          </p>
        </div>

        <div className="bg-gray-800 rounded-lg p-8 shadow-xl border border-gray-700">
          <div className="mb-6">
            <label className="block text-sm font-medium mb-2">
              Select Broker Template
            </label>
            <select
              value={selectedTemplate}
              onChange={(e) => setSelectedTemplate(e.target.value as BrokerTemplate)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="unified_v1">Unified CSV v1</option>
              <option value="webull_v1">Webull v1</option>
              <option value="robinhood_v1">Robinhood v1</option>
            </select>
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium mb-2">
              Upload CSV File
            </label>
            <div className="relative">
              <input
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-blue-600 file:text-white hover:file:bg-blue-700 file:cursor-pointer"
              />
            </div>
            {file && (
              <p className="text-sm text-gray-400 mt-2">
                Selected: {file.name}
              </p>
            )}
          </div>

          {error && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mb-6 p-4 bg-red-900/50 border border-red-700 rounded-lg text-red-200"
            >
              {error}
            </motion.div>
          )}

          <button
            onClick={handleUpload}
            disabled={uploading || !file}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-lg transition-colors duration-200"
          >
            {uploading ? 'Uploading...' : 'Upload & Analyze'}
          </button>

          <div className="mt-6 pt-6 border-t border-gray-700">
            <button
              onClick={handleViewDemo}
              className="w-full bg-gray-700 hover:bg-gray-600 text-white font-semibold py-3 rounded-lg transition-colors duration-200"
            >
              View Creator Demo
            </button>
          </div>
        </div>

        <div className="mt-8 text-center text-sm text-gray-500">
          <p>Supported: USD equities/ETFs (long & short)</p>
          <p>FIFO matching • Realized P&L only • No fees/dividends</p>
        </div>
      </motion.div>
    </div>
  );
}
