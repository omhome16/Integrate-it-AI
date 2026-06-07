interface Props {
  score: number;
}

export function HealthGauge({ score }: Props) {
  const radius = 52;
  const circumference = 2 * Math.PI * radius;
  const arc = circumference * 0.74;
  const offset = arc - (score / 100) * arc;

  return (
    <div className="health-gauge">
      <svg width="136" height="136" viewBox="0 0 136 136">
        <circle
          cx="68"
          cy="68"
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.08)"
          strokeWidth="12"
          strokeLinecap="round"
          strokeDasharray={`${arc} ${circumference}`}
          transform="rotate(137 68 68)"
        />
        <circle
          cx="68"
          cy="68"
          r={radius}
          fill="none"
          stroke="white"
          strokeWidth="12"
          strokeLinecap="round"
          strokeDasharray={`${arc} ${circumference}`}
          strokeDashoffset={offset}
          transform="rotate(137 68 68)"
        />
        <text x="68" y="65" textAnchor="middle" className="gauge-number">
          {score}
        </text>
        <text x="68" y="88" textAnchor="middle" className="gauge-label">
          health
        </text>
      </svg>
    </div>
  );
}
