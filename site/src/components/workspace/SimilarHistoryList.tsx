import { Link } from 'react-router-dom';
import { encodedName, toDisplay } from '../../lib/utils';
import { EmptyState } from '../common/EmptyState';

type SimilarHistoryListProps = {
  comparisons: Record<string, unknown>[];
  repoName: string;
};

export function SimilarHistoryList({ comparisons, repoName }: SimilarHistoryListProps) {
  if (!comparisons.length) {
    return <EmptyState title="暂无相似历史项目数据" message="请先完成 target 仓库分析和历史项目检索。" />;
  }
  return (
    <div className="similar-list">
      {comparisons.slice(0, 6).map((item, index) => {
        const name = toDisplay(item.history_repo_name ?? item.repo_name ?? item.name);
        return (
          <div className="similar-card" key={`${name}-${index}`}>
            <div>
              <span>#{index + 1}</span>
              <strong>{name}</strong>
            </div>
            <p>{toDisplay(item.similarity_summary ?? item.reason ?? item.summary)}</p>
            <dl>
              <div><dt>学校</dt><dd>{toDisplay(item.school)}</dd></div>
              <div><dt>年份</dt><dd>{toDisplay(item.year)}</dd></div>
              <div><dt>相似度</dt><dd>{toDisplay(item.similarity_score ?? item.hybrid_score)}</dd></div>
            </dl>
            <Link className="button button--subtle" to={`/compare/${encodedName(repoName)}`}>查看对比</Link>
          </div>
        );
      })}
    </div>
  );
}
