import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [status, setStatus] = useState('checking...')

  useEffect(() => {
    // Check backend health on mount
    fetch('http://localhost:8000/health')
      .then(res => res.json())
      .then(data => setStatus(data.status))
      .catch(() => setStatus('disconnected'))
  }, [])

  return (
    <div className="App">
      <header className="App-header">
        <h1>Stupid Chat Bot</h1>
        <p>Backend Status: {status}</p>
        <p className="info">
          This is a simple, straightforward AI-powered chat application.
        </p>
      </header>
    </div>
  )
}

export default App
