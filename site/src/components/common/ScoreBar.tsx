export function ScoreBar({ label, score }: { label: string; score?: number }) {
  const value = score ?? 0;
  return (
    <div className="score-bar">
      <div className="score-bar__head">
        <span>{label}</span>
        <strong>{score === undefined ? '暂无数据' : `${score} / 100`}</strong>
      </div>
      <div className="score-bar__track" aria-hidden="true">
        <span style={{ width: `${Math.max(0, Math.min(100, value))}%` }} />
      </div>
    </div>
  );
}
