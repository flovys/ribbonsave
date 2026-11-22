import { useState, useEffect } from 'react'
import { Clock, ExternalLink, Trash2 } from 'lucide-react'

const PLATFORM_EMOJI = {
  youtube: '▶',
  tiktok: '♪',
  instagram: '📷',
  twitter: '𝕏',
  facebook: 'f',
}

function timeAgo(ts) {
  const diff = Date.now() - ts
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

export default function RecentDownloads() {
  const [items, setItems] = useState([])

  useEffect(() => {
    try {
      const stored = JSON.parse(localStorage.getItem('ribbonsave_recent') || '[]')
      setItems(stored)
    } catch {
      setItems([])
    }
  }, [])

  const clearAll = () => {
    localStorage.removeItem('ribbonsave_recent')
    setItems([])
  }

  if (items.length === 0) return null

  return (
    <div className="mt-10 w-full max-w-2xl animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
      <div className="glass-card p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-display text-lg font-semibold text-dusty-mauve flex items-center gap-2">
            <Clock className="w-4 h-4 text-rose-pink" />
            Recent Downloads
          </h3>
          <button
            onClick={clearAll}
            className="text-xs text-dusty-mauve/40 hover:text-berry-pink flex items-center gap-1 transition-colors"
          >
            <Trash2 className="w-3 h-3" />
            Clear
          </button>
        </div>

        <div className="space-y-2">
          {items.map((item, idx) => (
            <div
              key={idx}
              className="flex items-center gap-3 px-3 py-2.5 rounded-xl bg-blush/50 hover:bg-pastel-pink/20
                         transition-all duration-200"
            >
              <span className="text-lg w-6 text-center shrink-0">
                {PLATFORM_EMOJI[item.platform] || '🌐'}
              </span>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-dusty-mauve truncate">
                  {item.title}
                </p>
                <p className="text-xs text-dusty-mauve/40">
                  {item.type === 'audio' ? '🎵 Audio' : '🎬 Video'} · {timeAgo(item.timestamp)}
                </p>
              </div>
              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="p-1.5 rounded-lg text-dusty-mauve/30 hover:text-rose-pink hover:bg-rose-pink/10 transition-all"
                title="Open original"
              >
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
