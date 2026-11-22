import { Heart } from 'lucide-react'

export default function Footer() {
  return (
    <footer className="w-full py-6 text-center border-t border-pastel-pink/20 bg-white/30 backdrop-blur-sm">
      <p className="text-sm text-dusty-mauve/50 font-body flex items-center justify-center gap-1.5">
        Made by <span className="font-display font-semibold text-dusty-mauve/70">RibbonSave</span>
      </p>
      <p className="text-xs text-dusty-mauve/30 mt-1">
        For personal use only. Respect content creators' rights 🎀
      </p>
    </footer>
  )
}
