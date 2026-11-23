import { useState, useEffect } from 'react'
import {
  Download,
  Music,
  Film,
  Image as ImageIcon,
  Loader2,
  Archive,
  FolderDown,
  Eye,
  X,
  ChevronLeft,
  ChevronRight,
  Sparkles
} from 'lucide-react'

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

  // State untuk Lightbox / Modal Preview foto
  const [previewIndex, setPreviewIndex] = useState(null)

  useEffect(() => {
    if (!hasVideo && activeTab === 'video') {
      setActiveTab(hasImages ? 'image' : (hasAudio ? 'audio' : 'video'))
    }
  }, [hasVideo, hasImages, hasAudio, activeTab])

  // Keyboard navigation untuk lightbox modal
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (previewIndex === null) return
      if (e.key === 'Escape') setPreviewIndex(null)
      else if (e.key === 'ArrowRight' && imagesList.length > 1) {
        setPreviewIndex((prev) => (prev + 1) % imagesList.length)
      } else if (e.key === 'ArrowLeft' && imagesList.length > 1) {
        setPreviewIndex((prev) => (prev - 1 + imagesList.length) % imagesList.length)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [previewIndex])

  const platform = PLATFORM_ICONS[info.platform] || { emoji: '🌐', label: info.platform, color: 'bg-gray-100 text-gray-500' }

  const imagesList = info.images && info.images.length > 0
    ? info.images
    : (info.thumbnail ? [{
        format_id: 'thumb_main',
        url: info.thumbnail,
        thumbnail_url: info.thumbnail,
        quality_label: 'Thumbnail / Cover HD',
        ext: 'jpg',
        resolution: 'HD',
        idx: 1
      }] : [])

  const isMultiPhoto = imagesList.length > 1

  return (
    <div className="mt-8 w-full max-w-2xl animate-fade-in-up">
      <div className="glass-card overflow-hidden">
        {/* Header - Thumbnail + Info */}
        <div className="flex flex-col sm:flex-row gap-4 p-5 pb-4">
          {/* Main Thumbnail Preview */}
          {info.thumbnail && (
            <div className="sm:w-48 w-full shrink-0">
              <div
                onClick={() => {
                  if (imagesList.length > 0) setPreviewIndex(0)
                }}
                className={`relative rounded-2xl overflow-hidden border-2 border-pastel-pink/40 shadow-pink-soft group ${
                  imagesList.length > 0 ? 'cursor-pointer' : ''
                }`}
                title={imagesList.length > 0 ? 'Klik untuk preview gambar' : ''}
              >
                <img
                  src={info.thumbnail}
                  alt={info.title}
                  className="w-full h-auto object-cover aspect-video transition-transform duration-300 group-hover:scale-105"
                />
                {imagesList.length > 0 && (
                  <div className="absolute inset-0 bg-dusty-mauve/25 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                    <span className="bg-white/90 text-dusty-mauve text-xs px-2.5 py-1 rounded-full font-bold flex items-center gap-1 shadow">
                      <Eye className="w-3.5 h-3.5 text-rose-pink" /> Preview
                    </span>
                  </div>
                )}
                {info.duration_formatted && (
                  <span className="absolute bottom-2 right-2 bg-black/60 text-white text-xs px-2 py-0.5 rounded-lg font-body">
                    {info.duration_formatted}
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Info Details */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold ${platform.color}`}>
                {platform.emoji} {platform.label}
              </span>
              {isMultiPhoto && (
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-pink/15 text-berry-pink border border-rose-pink/30">
                  <Sparkles className="w-3 h-3 text-berry-pink" />
                  Mode Carousel ({imagesList.length} Slide)
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

        {/* Tabs - Video, Audio, Foto */}
        <div className="flex border-t border-pastel-pink/30 bg-white/40">
          {hasVideo && (
            <button
              onClick={() => setActiveTab('video')}
              className={`flex-1 py-3 text-sm font-semibold flex items-center justify-center gap-2 transition-all duration-300
                ${activeTab === 'video'
                  ? 'text-berry-pink border-b-2 border-berry-pink bg-pastel-pink/15'
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
                  ? 'text-berry-pink border-b-2 border-berry-pink bg-pastel-pink/15'
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
                  ? 'text-berry-pink border-b-2 border-berry-pink bg-pastel-pink/15'
                  : 'text-dusty-mauve/50 hover:text-dusty-mauve hover:bg-pastel-pink/5'}`}
            >
              <ImageIcon className="w-4 h-4" />
              {isMultiPhoto ? `Foto (${imagesList.length})` : 'Gambar (JPG)'}
            </button>
          )}
        </div>

        {/* Format List / Tab Contents */}
        <div className="p-4 sm:p-5 space-y-3">
          {downloading && (
            <div className="flex flex-col items-center justify-center gap-3 py-6 px-4 bg-blush/80 rounded-2xl border border-pastel-pink/40 animate-pulse">
              <div className="w-10 h-10 rounded-full bg-rose-pink/20 flex items-center justify-center">
                <Loader2 className="w-6 h-6 animate-spin text-berry-pink" />
              </div>
              <span className="font-semibold text-sm text-dusty-mauve text-center">
                {downloadProgress || 'Processing download... 🎀'}
              </span>
            </div>
          )}

          {/* TAB 1: VIDEO */}
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

          {/* TAB 2: AUDIO */}
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

          {/* TAB 3: IMAGES / MULTI-PHOTO SLIDES */}
          {!downloading && activeTab === 'image' && hasImages && (
            <div className="space-y-3">
              {/* === PENINGKATAN 2: TOMBOL UNIVERSAL "DOWNLOAD ALL (.ZIP)" === */}
              {isMultiPhoto && (
                <div className="p-4 sm:p-5 rounded-3xl bg-gradient-to-r from-pastel-pink/35 via-blush to-rose-pink/25 border-2 border-pastel-pink/60 shadow-pink-soft flex flex-col sm:flex-row items-center justify-between gap-4 animate-fade-in-up">
                  <div className="flex items-center gap-3.5 w-full sm:w-auto">
                    <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-rose-pink to-berry-pink text-white flex items-center justify-center shrink-0 shadow-md">
                      <Archive className="w-6 h-6" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="text-sm sm:text-base font-bold text-dusty-mauve">
                          Unduh Semua ({imagesList.length} Foto) .ZIP
                        </h4>
                        <span className="text-[11px] px-2 py-0.5 rounded-full bg-berry-pink/15 text-berry-pink font-semibold">
                          Universal ✨
                        </span>
                      </div>
                      <p className="text-xs text-dusty-mauve/70 mt-0.5">
                        Simpan seluruh slide foto dalam 1 file arsip .ZIP beresolusi tinggi
                      </p>
                    </div>
                  </div>

                  <button
                    onClick={() => onDownload(info.url, null, 'zip', null, info.title, imagesList)}
                    disabled={downloading}
                    className="btn-primary w-full sm:w-auto flex items-center justify-center gap-2 py-3 px-5 text-sm shrink-0 whitespace-nowrap shadow-md hover:shadow-pink-hover"
                  >
                    <FolderDown className="w-4 h-4" />
                    <span>Download All (.ZIP)</span>
                  </button>
                </div>
              )}

              {/* Header Label Daftar Slide */}
              <div className="flex items-center justify-between px-1 text-xs font-semibold text-dusty-mauve/60">
                <span>
                  {isMultiPhoto
                    ? `Daftar Slide Foto (${imagesList.length} item):`
                    : 'Gambar Tersedia:'}
                </span>
                {isMultiPhoto && (
                  <span className="text-[11px] text-berry-pink font-medium">
                     Klik foto untuk melihat ukuran penuh
                  </span>
                )}
              </div>

              {/* === PENINGKATAN 1: DAFTAR SLIDE DENGAN PREVIEW THUMBNAIL UNIVERSAL === */}
              <div className="space-y-2.5">
                {imagesList.map((img, idx) => (
                  <div
                    key={idx}
                    className="w-full flex items-center justify-between p-3 sm:p-3.5 rounded-2xl
                               bg-blush/60 hover:bg-pastel-pink/25 border border-pastel-pink/30
                               transition-all duration-300 hover:shadow-sm group"
                  >
                    <div className="flex items-center gap-3.5 min-w-0">
                      {/* Thumbnail Preview */}
                      <div
                        onClick={() => setPreviewIndex(idx)}
                        className="w-14 h-14 sm:w-16 sm:h-16 rounded-xl overflow-hidden border-2 border-pastel-pink/50 bg-pastel-pink/10 shrink-0 relative cursor-pointer group/thumb shadow-sm"
                        title="Klik untuk melihat preview foto"
                      >
                        <img
                          src={img.thumbnail_url || img.url}
                          alt={img.quality_label || `Foto ${idx + 1}`}
                          className="w-full h-full object-cover transition-transform duration-300 group-hover/thumb:scale-110"
                          loading="lazy"
                          onError={(e) => {
                            e.currentTarget.style.display = 'none'
                            if (e.currentTarget.nextSibling) e.currentTarget.nextSibling.style.display = 'flex'
                          }}
                        />
                        <div className="hidden w-full h-full items-center justify-center bg-rose-pink/10 text-rose-pink">
                          <ImageIcon className="w-6 h-6" />
                        </div>
                        {/* Hover Overlay Icon */}
                        <div className="absolute inset-0 bg-dusty-mauve/30 opacity-0 group-hover/thumb:opacity-100 transition-opacity flex items-center justify-center">
                          <Eye className="w-4 h-4 text-white drop-shadow" />
                        </div>
                      </div>

                      {/* Detail Foto */}
                      <div className="text-left min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-sm font-bold text-dusty-mauve truncate">
                            {img.quality_label || `Foto ${idx + 1}`}
                          </span>
                          {isMultiPhoto && (
                            <span className="text-[11px] font-semibold px-2 py-0.5 rounded-md bg-pastel-pink/40 text-dusty-mauve/80">
                              Slide {idx + 1}/{imagesList.length}
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-dusty-mauve/60 mt-1 flex items-center gap-2">
                          <span>{img.resolution ? `${img.resolution}` : 'HD Quality'}</span>
                          <span>·</span>
                          <span className="uppercase text-[10px] font-bold px-1.5 py-0.5 rounded bg-rose-pink/10 text-rose-pink">
                            .{img.ext || 'jpg'}
                          </span>
                        </p>
                      </div>
                    </div>

                    {/* Tombol Aksi Kanan */}
                    <div className="flex items-center gap-2 shrink-0 ml-3">
                      <button
                        onClick={() => setPreviewIndex(idx)}
                        className="p-2 sm:px-3 sm:py-2 rounded-xl bg-white/70 hover:bg-pastel-pink/40 text-dusty-mauve/70 hover:text-dusty-mauve border border-pastel-pink/30 text-xs font-semibold flex items-center gap-1.5 transition-colors"
                        title="Preview Foto"
                      >
                        <Eye className="w-3.5 h-3.5 text-rose-pink" />
                        <span className="hidden sm:inline">Preview</span>
                      </button>

                      <button
                        onClick={() => onDownload(
                          info.url,
                          img.format_id,
                          'image',
                          img.url,
                          `${info.title || 'photo'}_${img.quality_label || `foto_${idx + 1}`}`
                        )}
                        className="px-3 py-2 rounded-xl bg-rose-pink/15 hover:bg-rose-pink text-dusty-mauve hover:text-white border border-rose-pink/30 text-xs font-bold flex items-center gap-1.5 transition-all duration-200 active:scale-95 shadow-sm group/btn"
                        title="Unduh foto ini"
                      >
                        <Download className="w-3.5 h-3.5 text-rose-pink group-hover/btn:text-white transition-colors" />
                        <span className="hidden sm:inline">Unduh</span>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* === LIGHTBOX / MODAL PREVIEW FOTO FULL RESOLUTION === */}
      {previewIndex !== null && imagesList[previewIndex] && (
        <div className="fixed inset-0 z-50 bg-dusty-mauve/60 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-in-up">
          <div className="glass-card max-w-3xl w-full p-4 sm:p-5 flex flex-col max-h-[90vh] relative shadow-2xl">
            {/* Modal Header */}
            <div className="flex items-center justify-between pb-3 mb-2 border-b border-pastel-pink/30">
              <div className="flex items-center gap-2">
                <span className="font-display font-bold text-base text-dusty-mauve">
                  {imagesList[previewIndex].quality_label || `Foto ${previewIndex + 1}`}
                </span>
                {isMultiPhoto && (
                  <span className="text-xs px-2 py-0.5 rounded-full bg-pastel-pink/30 text-dusty-mauve/80 font-medium">
                    {previewIndex + 1} dari {imagesList.length}
                  </span>
                )}
              </div>
              <button
                onClick={() => setPreviewIndex(null)}
                className="p-1.5 rounded-full hover:bg-pastel-pink/30 text-dusty-mauve/60 hover:text-dusty-mauve transition-colors"
                title="Tutup Preview"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Image Display */}
            <div className="relative flex-1 min-h-[250px] max-h-[60vh] flex items-center justify-center overflow-hidden rounded-2xl bg-black/5 p-2">
              <img
                src={imagesList[previewIndex].url}
                alt={imagesList[previewIndex].quality_label || 'Preview'}
                className="max-w-full max-h-[58vh] object-contain rounded-xl shadow-md"
              />

              {/* Prev & Next Controls for Multi-Photo */}
              {isMultiPhoto && (
                <>
                  <button
                    onClick={() => setPreviewIndex((prev) => (prev - 1 + imagesList.length) % imagesList.length)}
                    className="absolute left-3 top-1/2 -translate-y-1/2 p-2.5 rounded-full bg-white/80 hover:bg-white text-dusty-mauve hover:text-berry-pink shadow-md backdrop-blur-sm transition-all active:scale-95"
                    title="Foto Sebelumnya"
                  >
                    <ChevronLeft className="w-5 h-5" />
                  </button>
                  <button
                    onClick={() => setPreviewIndex((prev) => (prev + 1) % imagesList.length)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 p-2.5 rounded-full bg-white/80 hover:bg-white text-dusty-mauve hover:text-berry-pink shadow-md backdrop-blur-sm transition-all active:scale-95"
                    title="Foto Selanjutnya"
                  >
                    <ChevronRight className="w-5 h-5" />
                  </button>
                </>
              )}
            </div>

            {/* Modal Footer */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-3 mt-2 border-t border-pastel-pink/30">
              <span className="text-xs text-dusty-mauve/60">
                Format: <strong className="uppercase">.{imagesList[previewIndex].ext || 'jpg'}</strong> · Resolusi: <strong>{imagesList[previewIndex].resolution || 'HD'}</strong>
              </span>

              <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
                {isMultiPhoto && (
                  <button
                    onClick={() => {
                      setPreviewIndex(null)
                      onDownload(info.url, null, 'zip', null, info.title, imagesList)
                    }}
                    className="btn-secondary text-xs py-2 px-3 flex items-center gap-1.5"
                  >
                    <Archive className="w-3.5 h-3.5" />
                    Unduh Semua (.ZIP)
                  </button>
                )}

                <button
                  onClick={() => {
                    const currentImg = imagesList[previewIndex]
                    onDownload(
                      info.url,
                      currentImg.format_id,
                      'image',
                      currentImg.url,
                      `${info.title || 'photo'}_${currentImg.quality_label || `foto_${previewIndex + 1}`}`
                    )
                  }}
                  className="btn-primary text-xs py-2 px-4 flex items-center gap-1.5"
                >
                  <Download className="w-3.5 h-3.5" />
                  Unduh Foto Ini
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
