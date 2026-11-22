export default function LoadingBow() {
  return (
    <div className="mt-10 flex flex-col items-center gap-4 animate-fade-in-up">
      {/* Animated Ribbon / Bow */}
      <div className="relative">
        <svg
          className="w-20 h-20 animate-heartbeat"
          viewBox="0 0 120 120"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Left loop */}
          <path
            d="M60 55 C45 25, 10 30, 20 55 C10 75, 40 85, 60 65"
            stroke="#F48FB1"
            strokeWidth="3"
            fill="#F48FB1"
            fillOpacity="0.2"
            strokeLinecap="round"
          />
          {/* Right loop */}
          <path
            d="M60 55 C75 25, 110 30, 100 55 C110 75, 80 85, 60 65"
            stroke="#F48FB1"
            strokeWidth="3"
            fill="#F48FB1"
            fillOpacity="0.2"
            strokeLinecap="round"
          />
          {/* Center knot */}
          <circle cx="60" cy="60" r="7" fill="#EC407A" fillOpacity="0.6" />
          {/* Tails */}
          <path
            d="M55 67 L48 100"
            stroke="#F48FB1"
            strokeWidth="3"
            strokeLinecap="round"
          />
          <path
            d="M65 67 L72 100"
            stroke="#F48FB1"
            strokeWidth="3"
            strokeLinecap="round"
          />
        </svg>

        {/* Sparkles around the bow */}
        <span className="absolute -top-2 -right-2 text-lg animate-sparkle" style={{ animationDelay: '0s' }}>✨</span>
        <span className="absolute -bottom-1 -left-3 text-sm animate-sparkle" style={{ animationDelay: '0.5s' }}>✨</span>
        <span className="absolute top-1/2 -right-5 text-xs animate-sparkle" style={{ animationDelay: '1s' }}>💖</span>
      </div>

      <div className="text-center">
        <p className="font-display text-lg text-dusty-mauve italic">
          Fetching your media...
        </p>
        <p className="text-sm text-dusty-mauve/50 mt-1">
          Please wait a moment 🌸
        </p>
      </div>

      {/* Loading dots */}
      <div className="flex gap-1.5">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="w-2.5 h-2.5 rounded-full bg-rose-pink"
            style={{
              animation: 'bounce-soft 0.6s ease-in-out infinite',
              animationDelay: `${i * 0.15}s`,
            }}
          />
        ))}
      </div>
    </div>
  )
}
