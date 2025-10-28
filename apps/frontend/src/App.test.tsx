import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from './App'

describe('App', () => {
  it('renders the main heading', () => {
    render(<App />)
    expect(screen.getByText('Trading Dashboard MVP')).toBeInTheDocument()
  })

  it('displays backend status', () => {
    render(<App />)
    expect(screen.getByText(/Backend Status:/)).toBeInTheDocument()
  })
})
