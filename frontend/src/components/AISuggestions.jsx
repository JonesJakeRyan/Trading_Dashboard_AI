import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Sparkles, Loader2 } from 'lucide-react'
import axios from 'axios'

const AISuggestions = ({ metrics }) => {
  const [suggestions, setSuggestions] = useState('')
  const [displayedText, setDisplayedText] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchSuggestions = async () => {
      try {
        setIsLoading(true)
        setError(null)
        
        const response = await axios.post('http://localhost:8003/api/ai-suggestions', {
          metrics: metrics
        })
        
        setSuggestions(response.data.suggestions)
        setIsLoading(false)
      } catch (err) {
        console.error('Error fetching AI suggestions:', err)
        setError('Unable to generate suggestions at this time.')
        setIsLoading(false)
      }
    }

    if (metrics) {
      fetchSuggestions()
    }
  }, [metrics])

  // Typing animation effect
  useEffect(() => {
    if (!suggestions || isLoading) return

    let currentIndex = 0
    setDisplayedText('')

    const typingInterval = setInterval(() => {
      if (currentIndex < suggestions.length) {
        setDisplayedText(suggestions.slice(0, currentIndex + 1))
        currentIndex++
      } else {
        clearInterval(typingInterval)
      }
    }, 20) // Adjust speed here (lower = faster)

    return () => clearInterval(typingInterval)
  }, [suggestions, isLoading])

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5 }}
      className="bg-secondary rounded-lg p-6 border border-primary/10 h-full"
    >
      <div className="flex items-center space-x-3 mb-4">
        <div className="bg-primary/10 p-2 rounded-lg">
          <Sparkles className="w-5 h-5 text-primary" />
        </div>
        <h2 className="text-xl font-bold text-text">AI Suggestions</h2>
      </div>

      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-12">
          <Loader2 className="w-8 h-8 text-primary animate-spin mb-4" />
          <p className="text-sm text-text-dark">Analyzing your trading patterns...</p>
        </div>
      ) : error ? (
        <div className="text-red-400 text-sm">
          <p>{error}</p>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="text-text text-sm leading-relaxed whitespace-pre-wrap">
            {displayedText}
            {displayedText.length < suggestions.length && (
              <span className="inline-block w-2 h-4 bg-primary ml-1 animate-pulse" />
            )}
          </div>
        </div>
      )}
    </motion.div>
  )
}

export default AISuggestions
