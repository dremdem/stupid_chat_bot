import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
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

describe('App', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    vi.clearAllMocks()
  })

  it('renders without crashing', () => {
    render(<App />)
    // The app should render with its main container
    const appElement = document.querySelector('.app')
    expect(appElement).toBeInTheDocument()
  })

  it('renders ChatHeader component', () => {
    render(<App />)
    // ChatHeader should be present (it has a header element)
    const header = document.querySelector('header')
    expect(header).toBeInTheDocument()
  })

  it('renders InputBox component', () => {
    render(<App />)
    // InputBox should have a textarea
    const textarea = screen.getByRole('textbox')
    expect(textarea).toBeInTheDocument()
  })
})
