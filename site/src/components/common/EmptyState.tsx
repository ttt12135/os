type EmptyStateProps = {
  title?: string;
  message?: string;
};

export function EmptyState({ title = '暂无数据', message = '请先运行 Python 分析系统，生成 site/public/data 与 site/public/reports 后再刷新页面。' }: EmptyStateProps) {
  return (
    <div className="empty-state">
      <div className="empty-state__title">{title}</div>
      <p>{message}</p>
    </div>
  );
}
