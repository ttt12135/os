export function LoadingState({ label = '正在读取静态数据...' }: { label?: string }) {
  return <div className="loading-state">{label}</div>;
}
