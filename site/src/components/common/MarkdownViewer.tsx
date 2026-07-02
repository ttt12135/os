import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { EmptyState } from './EmptyState';

export function MarkdownViewer({ content, emptyTitle = '暂无分析报告' }: { content: string; emptyTitle?: string }) {
  if (!content.trim()) {
    return <EmptyState title={emptyTitle} message="当前仓库尚未生成 Markdown 报告。" />;
  }
  return (
    <article className="markdown-body">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </article>
  );
}
