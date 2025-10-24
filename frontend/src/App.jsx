import { useState } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Header from './components/Header'
import Dashboard from './pages/Dashboard'
import Upload from './pages/Upload'

function App() {
  const [metrics, setMetrics] = useState(null)
  const [fileName, setFileName] = useState(null)

  return (
    <Router>
      <div className="min-h-screen bg-background">
        <Header />
        <Routes>
          <Route 
            path="/" 
            element={
              <Upload 
                setMetrics={setMetrics} 
                setFileName={setFileName} 
              />
            } 
          />
          <Route 
            path="/dashboard" 
            element={
              <Dashboard 
                metrics={metrics} 
                fileName={fileName} 
              />
            } 
          />
        </Routes>
      </div>
    </Router>
  )
}

export default App
