import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ThemeProvider } from '../contexts/ThemeContext'
import App from '../App'

// Mock the websocket service to prevent actual connections during tests
vi.mock('../services/websocket', () => ({
  default: {
    connect: vi.fn(),
    disconnect: vi.fn(),
    onMessage: vi.fn(() => () => {}),
    onConnectionChange: vi.fn(() => () => {}),
    sendMessage: vi.fn(),
  },
}))

// Helper to render with providers
const renderWithProviders = (component) => {
  return render(<ThemeProvider>{component}</ThemeProvider>)
}

describe('App', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    vi.clearAllMocks()
  })

  it('renders without crashing', () => {
    renderWithProviders(<App />)
    // The app should render with its main container
    const appElement = document.querySelector('.app')
    expect(appElement).toBeInTheDocument()
  })

  it('renders ChatHeader component', () => {
    renderWithProviders(<App />)
    // ChatHeader should be present with title
    const title = screen.getByText('Stupid Chat Bot')
    expect(title).toBeInTheDocument()
  })

  it('renders InputBox component', () => {
    renderWithProviders(<App />)
    // InputBox should have a textarea
    const textarea = screen.getByRole('textbox')
    expect(textarea).toBeInTheDocument()
  })
})
