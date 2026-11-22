import { useState, useEffect } from 'react'
import { Download, Music, Film, Image as ImageIcon, Loader2 } from 'lucide-react'

function formatFileSize(bytes) {
  if (!bytes) return '~'
  const mb = bytes / (1024 * 1024)
  if (mb >= 1024) return `${(mb / 1024).toFixed(1)} GB`
  if (mb >= 1) return `${mb.toFixed(1)} MB`
  return `${(bytes / 1024).toFixed(0)} KB`
}

const PLATFORM_ICONS = {
  tiktok: { emoji: '♪', label: 'TikTok', color: 'bg-gray-100 text-gray-700' },
  instagram: { emoji: '📷', label: 'Instagram', color: 'bg-purple-100 text-purple-500' },
  twitter: { emoji: '𝕏', label: 'X/Twitter', color: 'bg-blue-100 text-blue-500' },
  facebook: { emoji: 'f', label: 'Facebook', color: 'bg-blue-100 text-blue-600' },
}

export default function VideoResultCard({ info, onDownload, downloading, downloadProgress }) {
  const hasVideo = Boolean(info.video_formats && info.video_formats.length > 0)
  const hasAudio = Boolean(info.audio_formats && info.audio_formats.length > 0)
  const hasImages = Boolean((info.images && info.images.length > 0) || info.thumbnail)

  const defaultTab = hasVideo ? 'video' : (hasImages ? 'image' : (hasAudio ? 'audio' : 'video'))
  const [activeTab, setActiveTab] = useState(defaultTab)

  useEffect(() => {
    if (!hasVideo && activeTab === 'video') {
      setActiveTab(hasImages ? 'image' : (hasAudio ? 'audio' : 'video'))
    }
  }, [hasVideo, hasImages, hasAudio, activeTab])

  const platform = PLATFORM_ICONS[info.platform] || { emoji: '🌐', label: info.platform, color: 'bg-gray-100 text-gray-500' }

  const imagesList = info.images && info.images.length > 0
    ? info.images
    : (info.thumbnail ? [{ format_id: 'thumb_main', url: info.thumbnail, quality_label: 'Thumbnail / Cover HD', ext: 'jpg' }] : [])

  return (
    <div className="mt-8 w-full max-w-2xl animate-fade-in-up">
      <div className="glass-card overflow-hidden">
        {/* Header - Thumbnail + Info */}
        <div className="flex flex-col sm:flex-row gap-4 p-5 pb-4">
          {/* Thumbnail */}
          {info.thumbnail && (
            <div className="sm:w-48 w-full shrink-0">
              <div className="relative rounded-2xl overflow-hidden border-2 border-pastel-pink/40 shadow-pink-soft group">
                <img
                  src={info.thumbnail}
                  alt={info.title}
                  className="w-full h-auto object-cover aspect-video"
                />
                {info.duration_formatted && (
                  <span className="absolute bottom-2 right-2 bg-black/60 text-white text-xs px-2 py-0.5 rounded-lg font-body">
                    {info.duration_formatted}
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold ${platform.color}`}>
                {platform.emoji} {platform.label}
              </span>
              {!hasVideo && hasImages && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-rose-pink/10 text-rose-pink">
                  🖼️ Mode Foto {imagesList.length > 1 ? `(${imagesList.length} Slide)` : ''}
                </span>
              )}
            </div>
            <h3 className="font-display text-lg font-semibold text-dusty-mauve leading-snug line-clamp-2 mb-1">
              {info.title}
            </h3>
            <p className="text-sm text-dusty-mauve/60 font-body">
              {info.uploader}
            </p>
            {info.view_count && (
              <p className="text-xs text-dusty-mauve/40 mt-1">
                {info.view_count.toLocaleString()} views
              </p>
            )}
          </div>
        </div>

        {/* Tabs - Hanya tampilkan tab yang kontennya tersedia */}
        <div className="flex border-t border-pastel-pink/30">
          {hasVideo && (
            <button
              onClick={() => setActiveTab('video')}
              className={`flex-1 py-3 text-sm font-semibold flex items-center justify-center gap-2 transition-all duration-300
                ${activeTab === 'video'
                  ? 'text-berry-pink border-b-2 border-berry-pink bg-pastel-pink/10'
                  : 'text-dusty-mauve/50 hover:text-dusty-mauve hover:bg-pastel-pink/5'}`}
            >
              <Film className="w-4 h-4" />
              Video (MP4)
            </button>
          )}
          {hasAudio && (
            <button
              onClick={() => setActiveTab('audio')}
              className={`flex-1 py-3 text-sm font-semibold flex items-center justify-center gap-2 transition-all duration-300
                ${activeTab === 'audio'
                  ? 'text-berry-pink border-b-2 border-berry-pink bg-pastel-pink/10'
                  : 'text-dusty-mauve/50 hover:text-dusty-mauve hover:bg-pastel-pink/5'}`}
            >
              <Music className="w-4 h-4" />
              Audio (MP3)
            </button>
          )}
          {hasImages && (
            <button
              onClick={() => setActiveTab('image')}
              className={`flex-1 py-3 text-sm font-semibold flex items-center justify-center gap-2 transition-all duration-300
                ${activeTab === 'image'
                  ? 'text-berry-pink border-b-2 border-berry-pink bg-pastel-pink/10'
                  : 'text-dusty-mauve/50 hover:text-dusty-mauve hover:bg-pastel-pink/5'}`}
            >
              <ImageIcon className="w-4 h-4" />
              {imagesList.length > 1 ? `Foto (${imagesList.length})` : 'Gambar (JPG)'}
            </button>
          )}
        </div>

        {/* Format List */}
        <div className="p-4 space-y-2">
          {downloading && (
            <div className="flex items-center justify-center gap-2 py-4 text-rose-pink">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span className="font-medium text-sm">{downloadProgress || 'Processing...'}</span>
            </div>
          )}

          {!downloading && activeTab === 'video' && hasVideo && (
            <>
              {(info.platform === 'tiktok' || info.platform === 'instagram') && (
                <div className="text-xs text-berry-pink/70 bg-berry-pink/5 rounded-xl px-3 py-2 mb-2 text-center">
                  ✨ No watermark version will be downloaded when available
                </div>
              )}
              {info.video_formats.map((fmt, idx) => (
                <button
                  key={idx}
                  onClick={() => onDownload(info.url, fmt.format_id, 'video', null, info.title)}
                  className="w-full flex items-center justify-between px-4 py-3 rounded-2xl
                             bg-blush/50 hover:bg-pastel-pink/30 border border-pastel-pink/20
                             transition-all duration-300 hover:scale-[1.01] active:scale-[0.99] group"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-rose-pink/10 flex items-center justify-center">
                      <Film className="w-4 h-4 text-rose-pink" />
                    </div>
                    <div className="text-left">
                      <span className="text-sm font-semibold text-dusty-mauve">
                        {fmt.quality_label}
                      </span>
                      <span className="text-xs text-dusty-mauve/50 ml-2">.{fmt.ext}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-dusty-mauve/40">{formatFileSize(fmt.filesize)}</span>
                    <Download className="w-4 h-4 text-rose-pink group-hover:text-berry-pink transition-colors" />
                  </div>
                </button>
              ))}
            </>
          )}

          {!downloading && activeTab === 'audio' && hasAudio && (
            <>
              {info.audio_formats.map((fmt, idx) => (
                <button
                  key={idx}
                  onClick={() => onDownload(info.url, fmt.format_id, 'audio', null, info.title)}
                  className="w-full flex items-center justify-between px-4 py-3 rounded-2xl
                             bg-blush/50 hover:bg-pastel-pink/30 border border-pastel-pink/20
                             transition-all duration-300 hover:scale-[1.01] active:scale-[0.99] group"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-rose-pink/10 flex items-center justify-center">
                      <Music className="w-4 h-4 text-rose-pink" />
                    </div>
                    <div className="text-left">
                      <span className="text-sm font-semibold text-dusty-mauve">
                        MP3 — {fmt.quality_label}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-dusty-mauve/40">{formatFileSize(fmt.filesize)}</span>
                    <Download className="w-4 h-4 text-rose-pink group-hover:text-berry-pink transition-colors" />
                  </div>
                </button>
              ))}
            </>
          )}

          {!downloading && activeTab === 'image' && hasImages && (
            <>
              {imagesList.length > 1 && (
                <div className="text-xs text-berry-pink/70 bg-berry-pink/5 rounded-xl px-3 py-2 mb-2 text-center">
                  ✨ Terdapat {imagesList.length} foto/slide yang siap diunduh:
                </div>
              )}
              {imagesList.map((img, idx) => (
                <button
                  key={idx}
                  onClick={() => onDownload(
                    info.url,
                    img.format_id,
                    'image',
                    img.url,
                    `${info.title || 'photo'}_${img.quality_label || `foto_${idx + 1}`}`
                  )}
                  className="w-full flex items-center justify-between px-4 py-3 rounded-2xl
                             bg-blush/50 hover:bg-pastel-pink/30 border border-pastel-pink/20
                             transition-all duration-300 hover:scale-[1.01] active:scale-[0.99] group"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-rose-pink/10 flex items-center justify-center">
                      <ImageIcon className="w-4 h-4 text-rose-pink" />
                    </div>
                    <div className="text-left">
                      <span className="text-sm font-semibold text-dusty-mauve">
                        {img.quality_label || `Foto ${idx + 1}`}
                      </span>
                      {img.resolution && (
                        <span className="text-xs text-dusty-mauve/50 ml-2">
                          ({img.resolution})
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-dusty-mauve/40">.{img.ext || 'jpg'}</span>
                    <Download className="w-4 h-4 text-rose-pink group-hover:text-berry-pink transition-colors" />
                  </div>
                </button>
              ))}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
