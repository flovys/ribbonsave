import { useState } from 'react'
import { ClipboardPaste, X, Search, Sparkles } from 'lucide-react'

const PLATFORM_BADGES = [
  { name: 'TikTok', color: 'bg-gray-100 text-gray-700', icon: '♪' },
  { name: 'Instagram', color: 'bg-purple-100 text-purple-500', icon: '📷' },
  { name: 'X / Twitter', color: 'bg-blue-100 text-blue-500', icon: '𝕏' },
  { name: 'Facebook', color: 'bg-blue-100 text-blue-600', icon: 'f' },
]

export default function UrlInputCard({ onFetch, loading }) {
  const [url, setUrl] = useState('')

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText()
      setUrl(text)
    } catch {
      // Clipboard API not available or permission denied
    }
  }

  const handleClear = () => setUrl('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (url.trim()) {
      onFetch(url.trim())
    }
  }

  return (
    <div className="w-full max-w-2xl relative animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
      {/* Ribbon SVG - Top Right */}
      <svg
        className="absolute -top-6 -right-6 w-16 h-16 text-rose-pink opacity-60 animate-ribbon-sway"
        viewBox="0 0 100 100"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          d="M50 20 C30 20, 10 35, 25 50 C10 65, 30 80, 50 65 C70 80, 90 65, 75 50 C90 35, 70 20, 50 20Z"
          fill="currentColor"
          fillOpacity="0.3"
        />
        <path
          d="M50 65 L45 90 M50 65 L55 90"
          stroke="currentColor"
          strokeWidth="3"
          strokeLinecap="round"
        />
        <circle cx="50" cy="50" r="6" fill="currentColor" fillOpacity="0.5" />
      </svg>

      {/* Ribbon SVG - Bottom Left */}
      <svg
        className="absolute -bottom-6 -left-6 w-14 h-14 text-pastel-pink opacity-50 animate-ribbon-sway"
        style={{ animationDelay: '1.5s' }}
        viewBox="0 0 100 100"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          d="M50 25 C35 25, 15 38, 28 50 C15 62, 35 75, 50 62 C65 75, 85 62, 72 50 C85 38, 65 25, 50 25Z"
          fill="currentColor"
          fillOpacity="0.4"
        />
        <path
          d="M50 62 L44 85 M50 62 L56 85"
          stroke="currentColor"
          strokeWidth="3"
          strokeLinecap="round"
        />
        <circle cx="50" cy="48" r="5" fill="currentColor" fillOpacity="0.5" />
      </svg>

      <div className="glass-card p-6 md:p-8">
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          {/* Input Row */}
          <div className="flex gap-2">
            <div className="relative flex-1">
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="Paste your video or image link here... 🌸"
                className="w-full px-5 py-3.5 pr-10 rounded-2xl border-2 border-pastel-pink/50
                           bg-white/90 text-dusty-mauve placeholder-dusty-mauve/40
                           font-body text-base
                           focus:outline-none focus:border-rose-pink focus:ring-4 focus:ring-rose-pink/20
                           transition-all duration-300"
              />
              {url && (
                <button
                  type="button"
                  onClick={handleClear}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-full
                             text-dusty-mauve/40 hover:text-berry-pink hover:bg-pastel-pink/30
                             transition-all duration-200"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
            <button
              type="button"
              onClick={handlePaste}
              className="btn-secondary flex items-center gap-1.5 shrink-0"
              title="Paste from clipboard"
            >
              <ClipboardPaste className="w-4 h-4" />
              <span className="hidden sm:inline">Paste</span>
            </button>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading || !url.trim()}
            className="btn-primary flex items-center justify-center gap-2 py-3.5 text-lg
                       disabled:opacity-50 disabled:cursor-not-allowed
                       hover:scale-[1.02] active:scale-[0.98] transition-transform"
          >
            {loading ? (
              <>
                <Sparkles className="w-5 h-5 animate-sparkle" />
                Fetching...
              </>
            ) : (
              <>
                <Search className="w-5 h-5" />
                Fetch Media
              </>
            )}
          </button>
        </form>

        {/* Platform Badges */}
        <div className="mt-5 flex flex-wrap items-center justify-center gap-2">
          <span className="text-xs text-dusty-mauve/50 font-medium mr-1">Supported:</span>
          {PLATFORM_BADGES.map((p) => (
            <span
              key={p.name}
              className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold ${p.color}`}
            >
              <span>{p.icon}</span>
              {p.name}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}
