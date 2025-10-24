import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import FileUpload from '../components/FileUpload'
import { AlertCircle, CheckCircle, TrendingUp, DollarSign, Eye } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { API_URL } from '../config'

const Upload = ({ setMetrics, setFileName }) => {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)
  const [uploadMode, setUploadMode] = useState('single') // 'single' or 'combined'
  const [stocksFile, setStocksFile] = useState(null)
  const [optionsFile, setOptionsFile] = useState(null)
  const navigate = useNavigate()

  // Auto-load demo on first visit
  useEffect(() => {
    const hasVisited = localStorage.getItem('hasVisited')
    if (!hasVisited) {
      loadDemo()
      localStorage.setItem('hasVisited', 'true')
    }
  }, [])

  const loadDemo = async () => {
    setError('')
    setSuccess(false)
    setIsLoading(true)

    try {
      const response = await axios.get(`${API_URL}/api/demo`)

      if (response.data.success) {
        setMetrics(response.data.metrics)
        setFileName('Demo Account (Sample Data)')
        setSuccess(true)
        
        // Navigate to dashboard
        setTimeout(() => {
          navigate('/dashboard')
        }, 1500)
      }
    } catch (err) {
      console.error('Demo load error:', err)
      setError('Failed to load demo data')
    } finally {
      setIsLoading(false)
    }
  }

  const handleFileSelect = async (file) => {
    setIsLoading(true)
    setError(null)
    setSuccess(false)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await axios.post(`${API_URL}/api/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      console.log('Upload response:', response.data)
      
      if (response.data.success) {
        console.log('Setting metrics:', response.data.metrics)
        setMetrics(response.data.metrics)
        setFileName(response.data.filename)
        setSuccess(true)
        
        // Navigate to dashboard after a brief delay
        setTimeout(() => {
          navigate('/dashboard')
        }, 1500)
      } else {
        setError('Upload succeeded but no metrics returned')
      }
    } catch (err) {
      console.error('Upload error:', err)
      setError(
        err.response?.data?.detail || 
        'Failed to upload and process file. Please check the format and try again.'
      )
    } finally {
      setIsLoading(false)
    }
  }

  const handleCombinedUpload = async () => {
    if (!stocksFile && !optionsFile) {
      setError('Please select at least one file to upload')
      return
    }

    setIsLoading(true)
    setError(null)
    setSuccess(false)

    try {
      const formData = new FormData()
      if (stocksFile) formData.append('equities_file', stocksFile)
      if (optionsFile) formData.append('options_file', optionsFile)

      const response = await axios.post(`${API_URL}/api/upload/combined`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      if (response.data.success) {
        setMetrics(response.data.metrics)
        setFileName(`${stocksFile?.name || ''} + ${optionsFile?.name || ''}`)
        setSuccess(true)
        
        // Navigate to dashboard after a brief delay
        setTimeout(() => {
          navigate('/dashboard')
        }, 1500)
      }
    } catch (err) {
      console.error('Upload error:', err)
      setError(
        err.response?.data?.detail || 
        'Failed to upload and process files. Please check the format and try again.'
      )
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="container mx-auto px-6 py-12">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <h1 className="text-4xl font-bold text-text mb-4">
            Upload Your Trading History
          </h1>
          <p className="text-lg text-text-dark">
            Analyze your performance with professional-grade metrics and insights
          </p>
        </motion.div>

        {/* Mode Toggle */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="flex justify-center mb-8"
        >
          <div className="inline-flex bg-secondary rounded-lg p-1 border border-primary/20">
            <button
              onClick={() => setUploadMode('single')}
              className={`px-6 py-2 rounded-md text-sm font-medium transition-all ${
                uploadMode === 'single'
                  ? 'bg-primary text-background'
                  : 'text-text-dark hover:text-text'
              }`}
            >
              <TrendingUp className="w-4 h-4 inline mr-2" />
              Single File
            </button>
            <button
              onClick={() => setUploadMode('combined')}
              className={`px-6 py-2 rounded-md text-sm font-medium transition-all ${
                uploadMode === 'combined'
                  ? 'bg-primary text-background'
                  : 'text-text-dark hover:text-text'
              }`}
            >
              <DollarSign className="w-4 h-4 inline mr-2" />
              Stocks + Options
            </button>
          </div>
        </motion.div>

        {/* Upload Component */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          {uploadMode === 'single' ? (
            <FileUpload onFileSelect={handleFileSelect} isLoading={isLoading} />
          ) : (
            <div className="space-y-4">
              {/* Stocks File Upload */}
              <div className="bg-secondary/50 rounded-lg p-6 border border-primary/10">
                <label className="block text-sm font-medium text-text mb-3">
                  📈 Stocks CSV (Optional)
                </label>
                <input
                  type="file"
                  accept=".csv"
                  onChange={(e) => setStocksFile(e.target.files[0])}
                  className="block w-full text-sm text-text-dark
                    file:mr-4 file:py-2 file:px-4
                    file:rounded-md file:border-0
                    file:text-sm file:font-semibold
                    file:bg-primary file:text-background
                    hover:file:bg-primary-light
                    file:cursor-pointer cursor-pointer"
                />
                {stocksFile && (
                  <p className="mt-2 text-xs text-primary">
                    Selected: {stocksFile.name}
                  </p>
                )}
              </div>

              {/* Options File Upload */}
              <div className="bg-secondary/50 rounded-lg p-6 border border-primary/10">
                <label className="block text-sm font-medium text-text mb-3">
                  📊 Options CSV (Optional)
                </label>
                <input
                  type="file"
                  accept=".csv"
                  onChange={(e) => setOptionsFile(e.target.files[0])}
                  className="block w-full text-sm text-text-dark
                    file:mr-4 file:py-2 file:px-4
                    file:rounded-md file:border-0
                    file:text-sm file:font-semibold
                    file:bg-primary file:text-background
                    hover:file:bg-primary-light
                    file:cursor-pointer cursor-pointer"
                />
                {optionsFile && (
                  <p className="mt-2 text-xs text-primary">
                    Selected: {optionsFile.name}
                  </p>
                )}
              </div>

              {/* Upload Button */}
              <button
                onClick={handleCombinedUpload}
                disabled={isLoading || (!stocksFile && !optionsFile)}
                className="w-full bg-primary hover:bg-primary-light text-background font-semibold py-3 px-6 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? 'Analyzing...' : 'Analyze Combined Performance'}
              </button>
            </div>
          )}
        </motion.div>

        {/* Demo Button */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="mt-6 text-center"
        >
          <button
            onClick={loadDemo}
            disabled={isLoading}
            className="inline-flex items-center space-x-2 px-6 py-3 bg-secondary/50 hover:bg-secondary/70 
                     text-text rounded-lg transition-all duration-200 border border-primary/20
                     hover:border-primary/40 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Eye className="w-4 h-4" />
            <span>View Demo Dashboard</span>
          </button>
          <p className="text-xs text-text-dark mt-2">
            See a sample trading account with real metrics
          </p>
        </motion.div>

        {/* Success Message */}
        <AnimatePresence>
          {success && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="mt-6 bg-green-500/10 border border-green-500/30 rounded-lg p-4"
            >
              <div className="flex items-center space-x-3">
                <CheckCircle className="w-5 h-5 text-green-400" />
                <div>
                  <p className="text-sm font-medium text-green-400">
                    {isLoading ? 'Loading demo...' : 'Upload successful!'}
                  </p>
                  <p className="text-xs text-green-400/80">
                    Redirecting to your dashboard...
                  </p>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Error Message */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="mt-6 bg-red-500/10 border border-red-500/30 rounded-lg p-4"
            >
              <div className="flex items-start space-x-3">
                <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-red-400 mb-1">
                    Upload failed
                  </p>
                  <p className="text-xs text-red-400/80">
                    {error}
                  </p>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Instructions */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="mt-12 bg-secondary/50 rounded-lg p-6 border border-primary/10"
        >
          <h3 className="text-lg font-semibold text-text mb-4">
            {uploadMode === 'single' ? 'CSV Format Requirements' : 'Combined Upload Guide'}
          </h3>
          <div className="space-y-3 text-sm text-text-dark">
            {uploadMode === 'single' ? (
              <>
                <p>Your CSV should include the following columns:</p>
                <ul className="list-disc list-inside space-y-2 ml-4">
                  <li><span className="text-primary font-mono">Date</span> - Trade execution date</li>
                  <li><span className="text-primary font-mono">Symbol</span> - Stock/Option symbol</li>
                  <li><span className="text-primary font-mono">Quantity</span> - Number of shares/contracts</li>
                  <li><span className="text-primary font-mono">Price</span> - Execution price</li>
                  <li><span className="text-primary font-mono">Side</span> - Buy or Sell</li>
                  <li><span className="text-primary font-mono">Fees</span> - Commission/fees (optional)</li>
                </ul>
                <p className="mt-4 text-xs">
                  <span className="text-primary">Note:</span> The system automatically detects stocks vs options and handles different broker formats (Webull, TD Ameritrade, Interactive Brokers).
                </p>
              </>
            ) : (
              <>
                <p>Upload both your stocks and options trading history for combined analysis:</p>
                <ul className="list-disc list-inside space-y-2 ml-4">
                  <li><span className="text-primary">Stocks CSV</span> - Your stock trading history</li>
                  <li><span className="text-primary">Options CSV</span> - Multi-leg strategies (Iron Condors, Butterflies, Verticals, etc.)</li>
                </ul>
                <p className="mt-4">
                  The system will combine P&L from both sources and provide unified metrics including:
                </p>
                <ul className="list-disc list-inside space-y-1 ml-4 mt-2">
                  <li>Combined total P&L</li>
                  <li>Breakdown by stocks vs options</li>
                  <li>Unified win rate and expectancy</li>
                  <li>Overall Sharpe ratio and drawdown</li>
                </ul>
                <p className="mt-4 text-xs">
                  <span className="text-primary">Tip:</span> You can upload just one file type if you only trade stocks or options.
                </p>
              </>
            )}
          </div>
        </motion.div>
      </div>
    </div>
  )
}

export default Upload
