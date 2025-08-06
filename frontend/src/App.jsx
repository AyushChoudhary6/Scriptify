import { useState, useEffect, useCallback } from 'react'
import './App.css'
import React from 'react'

function App() {
  const [url, setUrl] = useState('')
  const [transcript, setTranscript] = useState('')
  const [isLoading, setLoading] = useState(false)
  const [isSidebarOpen, setSidebarOpen] = useState(false)
  const [error, setError] = useState('')
  const [copySuccess, setCopySuccess] = useState(false)
  const [progress, setProgress] = useState(0) // Progress percentage
  const [progressMessage, setProgressMessage] = useState('') // Progress message
  const [summaryType, setSummaryType] = useState('comprehensive') // New: summary type
  const [videoInfo, setVideoInfo] = useState(null) // New: video information

  // Reset copy success message after 3 seconds
  useEffect(() => {
    if (copySuccess) {
      const timer = setTimeout(() => {
        setCopySuccess(false)
      }, 3000)
      return () => clearTimeout(timer)
    }
  }, [copySuccess])

  const handleConvert = async () => {
    // Validate YouTube URL
    if (!url.includes('youtube.com') && !url.includes('youtu.be')) {
      setError('Please enter a valid YouTube URL')
      return
    }

    setLoading(true)
    setSidebarOpen(true)
    setError('')
    setCopySuccess(false)
    setProgress(0)
    setProgressMessage('Initializing...')

    try {
      console.log('Sending request to backend with URL:', url, 'using enhanced summarization')
      console.log('Summary type:', summaryType)

      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setProgress(prev => {
          if (prev < 90) {
            const newProgress = prev + Math.random() * 15
            if (newProgress < 15) {
              setProgressMessage('Initializing audio processing...')
            } else if (newProgress < 30) {
              setProgressMessage('Extracting high-quality audio...')
            } else if (newProgress < 45) {
              setProgressMessage('Analyzing speech patterns...')
            } else if (newProgress < 60) {
              setProgressMessage('Transcribing audio content...')
            } else if (newProgress < 75) {
              setProgressMessage('Detecting chapters and highlights...')
            } else {
              setProgressMessage('Generating intelligent summary...')
            }
            return Math.min(newProgress, 90)
          }
          return prev
        })
      }, 1000)

      // Use the new enhanced summarization endpoint
      const response = await fetch('/transcribe-summary/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          url, 
          summary_type: summaryType,
          include_timestamps: true, // Always include timestamps
          include_chapters: false,   // No chapters
          include_highlights: true
        }),
      })

      clearInterval(progressInterval)
      setProgress(95)
      setProgressMessage('Finalizing summary...')

      if (!response.ok) {
        const errorText = await response.text()
        console.error('Response error:', response.status, errorText)
        throw new Error(`HTTP error! Status: ${response.status}`)
      }

      const data = await response.json()
      
      if (data.error) {
        throw new Error(data.error)
      }
      
      setProgress(100)
      setProgressMessage('Complete!')
      setTranscript(data.text)
      setVideoInfo(data.video_info) // Store video information
      setError('') // Clear any previous errors on successful completion
      
      // Clear progress after a delay
      setTimeout(() => {
        setProgress(0)
        setProgressMessage('')
      }, 2000)
      
    } catch (error) {
      console.error('Error fetching transcript:', error)
      setError(error.message || 'Failed to convert video. Please try again.')
      setProgress(0)
      setProgressMessage('')
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(transcript)
      .then(() => {
        setCopySuccess(true)
      })
      .catch(() => {
        setError('Failed to copy text to clipboard')
      })
  }

  const handleDownload = () => {
    // Create a blob with the summary text
    const blob = new Blob([transcript], { type: 'text/plain' })
    // Create a URL for the blob
    const url = URL.createObjectURL(blob)
    // Create a temporary link element
    const a = document.createElement('a')
    a.href = url
    a.download = 'video-summary.txt'
    // Append the link to the body
    document.body.appendChild(a)
    // Click the link to trigger the download
    a.click()
    // Remove the link from the body
    document.body.removeChild(a)
    // Release the URL object
    URL.revokeObjectURL(url)
  }

  // Function to handle keyboard shortcut for paste and convert
  // Memoize the handler with useCallback to prevent recreating the function on every render
  const handleKeyDown = useCallback((e) => {
    // Check if Ctrl+V (Windows) or Cmd+V (Mac) was pressed
    if ((e.ctrlKey || e.metaKey) && e.key === 'v') {
      // Get clipboard data
      navigator.clipboard.readText()
        .then(text => {
          if (text.includes('youtube.com') || text.includes('youtu.be')) {
            setUrl(text)
            // Auto-convert after a short delay to allow state update
            setTimeout(() => {
              // We need to get the latest URL value here
              handleConvert()
            }, 500)
          }
        })
        .catch(err => {
          console.error('Failed to read clipboard:', err)
          setError('Failed to read from clipboard')
        })
    }
  }, []) // Empty dependency array as we'll handle url manually

  // Add event listener when component mounts
  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown)
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [handleKeyDown]) // Depend on the memoized handler

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-900 to-purple-900 text-white flex flex-col items-center">
      {/* Main content */}
      <div className="container mx-auto px-4 py-12 max-w-4xl">
                <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-cyan-400 to-pink-500 bg-clip-text text-transparent">
          YouTube to Intelligent Summary
        </h1>
        <p className="text-xl text-gray-300">
          Transform any YouTube video into a comprehensive intelligent summary with timestamps, key insights, and detailed analysis
        </p>

        <div className="bg-white/10 backdrop-blur-md p-8 rounded-lg shadow-2xl">
          <div className="flex flex-col md:flex-row gap-4">
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Paste YouTube URL here..."
              aria-label="YouTube URL input"
              className="flex-1 px-4 py-3 rounded-lg bg-white/5 border border-white/20 focus:outline-none focus:border-cyan-400 text-white placeholder-gray-400"
            />
            <div className="flex gap-2">
              <select
                value={summaryType}
                onChange={(e) => setSummaryType(e.target.value)}
                className="px-4 py-3 rounded-lg bg-white/5 border border-white/20 focus:outline-none focus:border-cyan-400 text-white"
                aria-label="Select summary type"
              >
                <option value="comprehensive">📊 Comprehensive</option>
                <option value="brief">⚡ Brief</option>
                <option value="bullets">📋 Bullet Points</option>
                <option value="academic">🎓 Academic</option>
              </select>
              <button
                onClick={handleConvert}
                disabled={isLoading}
                aria-label="Convert video"
                className="px-6 py-3 bg-gradient-to-r from-cyan-500 to-pink-500 rounded-lg font-bold hover:opacity-90 transition-all disabled:opacity-50"
              >
                {isLoading ? 'Converting...' : 'Convert'}
              </button>
            </div>
          </div>
          <p className="mt-4 text-sm text-gray-400">
            Get comprehensive intelligent video summaries with automatic timestamps, chapters, and key insights. Our AI analyzes the complete audio content to provide detailed, accurate summaries.
          </p>
        </div>

        <div className="mt-12 text-center">
          <h2 className="text-2xl font-semibold mb-4">How It Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white/5 p-6 rounded-lg">
              <div className="text-cyan-300 text-xl mb-2">1</div>
              <h3 className="font-medium mb-2">Paste URL</h3>
              <p className="text-sm text-gray-400">Copy the YouTube video URL and paste it in the box above</p>
            </div>
            <div className="bg-white/5 p-6 rounded-lg">
              <div className="text-cyan-300 text-xl mb-2">2</div>
              <h3 className="font-medium mb-2">AI Analysis</h3>
              <p className="text-sm text-gray-400">Our AI analyzes the complete audio content and generates comprehensive summaries</p>
            </div>
            <div className="bg-white/5 p-6 rounded-lg">
              <div className="text-cyan-300 text-xl mb-2">3</div>
              <h3 className="font-medium mb-2">Get Summary</h3>
              <p className="text-sm text-gray-400">Receive a detailed, intelligent summary with timestamps and key insights</p>
            </div>
          </div>
        </div>
      </div>

      {/* Sidebar */}
      <div 
        className={`fixed top-0 right-0 h-full w-full md:w-1/3 bg-gray-900 shadow-2xl transform transition-transform duration-300 ease-in-out overflow-auto z-50 ${
          isSidebarOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
        aria-hidden={!isSidebarOpen}
      >
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold">Intelligent Summary</h2>
            <button 
              onClick={() => setSidebarOpen(false)} 
              aria-label="Close summary sidebar"
              className="text-gray-400 hover:text-white"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          {isLoading ? (
            <div className="flex flex-col items-center justify-center h-64">
              {/* Enhanced Progress Indicator */}
              <div className="w-full max-w-md mb-6">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-cyan-300">Processing Video</span>
                  <span className="text-sm font-medium text-cyan-300">{Math.round(progress)}%</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2.5">
                  <div 
                    className="bg-gradient-to-r from-cyan-400 to-pink-500 h-2.5 rounded-full transition-all duration-500 ease-out"
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>
                <p className="text-center text-gray-400 mt-3 text-sm">{progressMessage}</p>
              </div>
              
              {/* Animated Processing Icon */}
              <div className="relative">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-400" role="status"></div>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-3 h-3 bg-cyan-400 rounded-full animate-pulse"></div>
                </div>
              </div>
              
              <p className="mt-4 text-gray-400 text-center max-w-sm">
                Our AI is analyzing your video to create an intelligent summary with timestamps and key insights...
              </p>
            </div>
          ) : (
            <>
              {transcript ? (
                <div>
                  {/* Video Information Display */}
                  {videoInfo && (
                    <div className="bg-gradient-to-r from-cyan-500/10 to-pink-500/10 rounded-lg p-4 mb-4 border border-cyan-500/20">
                      <h3 className="text-lg font-semibold mb-3 text-cyan-300">📹 Video Information</h3>
                      <div className="space-y-2 text-sm">
                        <div><span className="text-gray-400">Title:</span> <span className="text-white">{videoInfo.title}</span></div>
                        <div><span className="text-gray-400">Creator:</span> <span className="text-white">{videoInfo.uploader}</span></div>
                        <div><span className="text-gray-400">Duration:</span> <span className="text-white">{videoInfo.duration}</span></div>
                        <div><span className="text-gray-400">Views:</span> <span className="text-white">{videoInfo.view_count}</span></div>
                        <div><span className="text-gray-400">Published:</span> <span className="text-white">{videoInfo.upload_date}</span></div>
                      </div>
                    </div>
                  )}
                  
                  <div className="bg-white/5 rounded-lg p-4 mb-4">
                    <div className="flex flex-col gap-3 mb-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-300 font-medium">Summary</span>
                        {copySuccess && (
                          <span className="text-xs text-green-400" role="status">✓ Copied to clipboard!</span>
                        )}
                      </div>
                      <div className="flex gap-2">
                        <button 
                          onClick={handleCopy}
                          aria-label="Copy summary to clipboard"
                          className="text-sm bg-gradient-to-r from-cyan-500 to-blue-500 px-4 py-2 rounded hover:opacity-90 transition-all flex-1"
                        >
                          Copy Summary
                        </button>
                        <button 
                          onClick={handleDownload}
                          aria-label="Download summary as text file"
                          className="text-sm bg-gradient-to-r from-purple-500 to-pink-500 px-4 py-2 rounded hover:opacity-90 transition-all flex-1"
                        >
                          Download Summary
                        </button>
                      </div>
                    </div>
                    <div className="border-t border-white/10 pt-3">
                      <p className="text-gray-300 whitespace-pre-line">{transcript}</p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center text-gray-400 py-12">
                  No summary available yet. Convert a video to see the intelligent summary.
                </div>
              )}
              {error && (
                <div className="text-center text-red-500 py-4" role="alert">
                  {error}
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Overlay when sidebar is open */}
      {isSidebarOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        ></div>
      )}
    </div>
  )
}

export default App