import { Ribbon } from 'lucide-react'

export default function Navbar() {
  return (
    <nav className="w-full py-4 px-6 flex items-center justify-center gap-2 bg-white/50 backdrop-blur-sm border-b border-pastel-pink/30">
      <Ribbon className="w-6 h-6 text-rose-pink animate-ribbon-sway" />
      <span className="font-display text-2xl font-bold text-dusty-mauve">
        Ribbon<span className="text-gradient-pink">Save</span>
      </span>
      <span className="text-sm text-dusty-mauve/50 font-body ml-2 hidden sm:inline">
        🎀 media downloader
      </span>
    </nav>
  )
}
