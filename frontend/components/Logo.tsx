/**
 * Scintia symbol: a cold tomographic ring + an off-center warm emitting core
 * (docs/03_CHARTE_GRAPHIQUE.md §2). Decorative; pair with the wordmark for the
 * full lockup.
 */
export function Logo({
  size = 40,
  className,
}: {
  size?: number;
  className?: string;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      role="img"
      aria-label="Scintia"
      className={className}
    >
      <defs>
        <radialGradient id="scintia-core" cx="40%" cy="34%" r="64%">
          <stop offset="0%" stopColor="#FFE9C2" />
          <stop offset="26%" stopColor="#FFB13D" />
          <stop offset="54%" stopColor="#EC4899" />
          <stop offset="84%" stopColor="#6E6FFF" />
          <stop offset="100%" stopColor="#6E6FFF" stopOpacity="0" />
        </radialGradient>
        <linearGradient id="scintia-ring" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#34E3E3" />
          <stop offset="100%" stopColor="#6E6FFF" />
        </linearGradient>
      </defs>
      <circle
        cx="32"
        cy="32"
        r="22"
        fill="none"
        stroke="url(#scintia-ring)"
        strokeWidth="2.4"
        opacity="0.92"
      />
      <circle
        cx="32"
        cy="32"
        r="15.2"
        fill="none"
        stroke="#34E3E3"
        strokeWidth="1"
        opacity="0.22"
        strokeDasharray="3 6"
        strokeLinecap="round"
      />
      {/* Charter §9 signature motion: gentle breathing of the luminous core.
          Disabled under prefers-reduced-motion (globals.css). */}
      <circle
        cx="40.5"
        cy="25.5"
        r="13"
        fill="url(#scintia-core)"
        className="animate-breathe"
      />
      <circle cx="40.5" cy="25.5" r="7.4" fill="url(#scintia-core)" />
    </svg>
  );
}
