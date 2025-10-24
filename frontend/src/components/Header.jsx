import { Link, useLocation } from 'react-router-dom'

const Header = () => {
  const location = useLocation()

  return (
    <header className="bg-secondary border-b border-primary/20">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center space-x-3 group">
            <img 
              src="/Company_Logo1.png" 
              alt="Company Logo"
              className="w-14 h-14 object-contain group-hover:scale-105 transition-transform"
            />
            <div>
              <h1 className="text-xl font-bold text-text">
                Jones Software & Data
              </h1>
              <p className="text-xs text-text-dark">Trading Performance Dashboard</p>
            </div>
          </Link>
          
          <nav className="flex space-x-6">
            <Link
              to="/"
              className={`text-sm font-medium transition-colors ${
                location.pathname === '/'
                  ? 'text-primary'
                  : 'text-text hover:text-primary'
              }`}
            >
              Upload
            </Link>
            <Link
              to="/dashboard"
              className={`text-sm font-medium transition-colors ${
                location.pathname === '/dashboard'
                  ? 'text-primary'
                  : 'text-text hover:text-primary'
              }`}
            >
              Dashboard
            </Link>
          </nav>
        </div>
      </div>
    </header>
  )
}

export default Header
