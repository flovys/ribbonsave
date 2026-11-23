import { useState } from 'react'
import Navbar from './components/Navbar'
import UrlInputCard from './components/UrlInputCard'
import VideoResultCard from './components/VideoResultCard'
import LoadingBow from './components/LoadingBow'
import RecentDownloads from './components/RecentDownloads'
import Footer from './components/Footer'
import axios from 'axios'

const API_BASE = '/api'

function App() {
  const [videoInfo, setVideoInfo] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [downloading, setDownloading] = useState(false)
  const [downloadProgress, setDownloadProgress] = useState('')

  const handleFetchInfo = async (url) => {
    setLoading(true)
    setError(null)
    setVideoInfo(null)

    try {
      const response = await axios.post(`${API_BASE}/info`, { url })
      setVideoInfo({ ...response.data, url })
    } catch (err) {
      const detail = err.response?.data?.detail || 'Something went wrong 💔 Please check the URL and try again.'
      setError(detail)
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = async (url, formatId, type, imageUrl = null, title = null, images = null) => {
    setDownloading(true)
    let progressMsg = 'Processing video...'
    if (type === 'audio') progressMsg = 'Extracting audio (MP3)... 🎵'
    else if (type === 'image') progressMsg = 'Downloading image... 🖼️'
    else if (type === 'zip') {
      const count = images ? images.length : ''
      progressMsg = `Mempersiapkan ZIP (${count ? `${count} foto` : 'semua foto'})... 🎀`
    }
    setDownloadProgress(progressMsg)

    try {
      let endpoint = `${API_BASE}/download`
      let payload = { url, format_id: formatId, type, image_url: imageUrl, title, images }

      if (type === 'zip') {
        endpoint = `${API_BASE}/download-zip`
        payload = { url, title, images }
      }

      const response = await axios.post(
        endpoint,
        payload,
        { responseType: 'blob' }
      )

      // Extract filename from Content-Disposition header
      const contentDisposition = response.headers['content-disposition']
      let defaultName = 'video.mp4'
      if (type === 'audio') defaultName = 'audio.mp3'
      else if (type === 'image') defaultName = 'image.jpg'
      else if (type === 'zip') defaultName = `${title ? title.slice(0, 50) : 'photos'}.zip`
      let filename = defaultName

      if (contentDisposition) {
        const utf8Match = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i)
        if (utf8Match) {
          try {
            filename = decodeURIComponent(utf8Match[1])
          } catch {
            // fallback
          }
        } else {
          const filenameMatch = contentDisposition.match(/filename="?([^";]+)"?/i)
          if (filenameMatch) {
            filename = filenameMatch[1]
          }
        }
      }

      // Create download link
      const blob = new Blob([response.data])
      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = filename
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(downloadUrl)

      // Save to recent downloads
      saveToRecent({
        title: videoInfo?.title || 'Unknown',
        platform: videoInfo?.platform || 'unknown',
        type,
        url,
        timestamp: Date.now(),
      })
    } catch (err) {
      let detail = 'Download failed 💔 Please try again.'
      if (err.response?.data) {
        if (err.response.data instanceof Blob) {
          try {
            const text = await err.response.data.text()
            const parsed = JSON.parse(text)
            if (parsed.detail) detail = parsed.detail
          } catch {
            // keep fallback
          }
        } else if (err.response.data.detail) {
          detail = err.response.data.detail
        }
      }
      setError(detail)
    } finally {
      setDownloading(false)
      setDownloadProgress('')
    }
  }

  const saveToRecent = (item) => {
    try {
      const existing = JSON.parse(localStorage.getItem('ribbonsave_recent') || '[]')
      const updated = [item, ...existing.filter(e => e.url !== item.url)].slice(0, 5)
      localStorage.setItem('ribbonsave_recent', JSON.stringify(updated))
    } catch (e) {
      // localStorage not available
    }
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />

      <main className="flex-1 flex flex-col items-center px-4 pb-12">
        {/* Hero Section */}
        <div className="mt-10 mb-8 text-center animate-fade-in-up">
          <h1 className="font-display text-4xl md:text-5xl lg:text-6xl font-bold text-dusty-mauve mb-3">
            Ribbon<span className="text-gradient-pink">Save</span>
          </h1>
          <p className="font-display italic text-lg md:text-xl text-dusty-mauve/70">
            Media Downloader ✨
          </p>
        </div>

        {/* Input Card */}
        <UrlInputCard onFetch={handleFetchInfo} loading={loading} />

        {/* Loading State */}
        {loading && <LoadingBow />}

        {/* Error State */}
        {error && (
          <div className="mt-6 glass-card px-6 py-4 max-w-xl w-full text-center animate-fade-in-up">
            <p className="text-berry-pink font-medium">{error}</p>
          </div>
        )}

        {/* Result Card */}
        {videoInfo && !loading && (
          <VideoResultCard
            info={videoInfo}
            onDownload={handleDownload}
            downloading={downloading}
            downloadProgress={downloadProgress}
          />
        )}

        {/* Recent Downloads */}
        <RecentDownloads />
      </main>

      <Footer />
    </div>
  )
}

export default App
