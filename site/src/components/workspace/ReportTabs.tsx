import { useEffect, useMemo, useState } from 'react';
import { EmptyState } from '../common/EmptyState';
import { MarkdownViewer } from '../common/MarkdownViewer';

type ReportTabId = 'description' | 'final';

export function ReportTabs({ description, final }: { description: string; final: string }) {
  const tabs = useMemo(() => {
    const available: Array<{ id: ReportTabId; label: string; content: string }> = [];
    if (final.trim()) available.push({ id: 'final', label: '最终分析报告', content: final });
    if (description.trim()) available.push({ id: 'description', label: '项目描述报告', content: description });
    return available;
  }, [description, final]);

  const [tab, setTab] = useState<ReportTabId>('final');

  useEffect(() => {
    if (!tabs.length) return;
    if (!tabs.some((item) => item.id === tab)) {
      setTab(tabs[0].id);
    }
  }, [tab, tabs]);

  if (!tabs.length) {
    return <EmptyState title="暂无分析报告" message="当前仓库尚未生成 Markdown 报告。" />;
  }

  const active = tabs.find((item) => item.id === tab) ?? tabs[0];

  return (
    <div>
      {tabs.length > 1 ? (
        <div className="tab-list">
          {tabs.map((item) => (
            <button key={item.id} className={tab === item.id ? 'tab is-active' : 'tab'} type="button" onClick={() => setTab(item.id)}>
              {item.label}
            </button>
          ))}
        </div>
      ) : null}
      <MarkdownViewer content={active.content} />
    </div>
  );
}
