import { ExternalLink } from 'lucide-react';
import { getLevel, getMetric, getRepoName, getRepoUrl, getSchool, getScope, getScore, getTeamCode, getTeamName, getTrack, getYear, type RepoRecord } from '../../lib/adapters';
import { ScoreBadge } from '../common/ScoreBadge';

export function RepositoryIdentityCard({ repo }: { repo: RepoRecord }) {
  const url = getRepoUrl(repo);
  const score = getScore(repo);
  const fields = [
    ['队伍名', getTeamName(repo)],
    ['队伍编号', getTeamCode(repo)],
    ['学校', getSchool(repo)],
    ['年份', getYear(repo)],
    ['Scope', getScope(repo)],
    ['Track', getTrack(repo)],
    ['Commit', getMetric(repo, ['commit', 'commit_hash', 'sha'])],
    ['分析时间', getMetric(repo, ['analysis_time', 'analyzed_at', 'generated_at'])],
    ['代码块数量', getMetric(repo, ['code_block_count', 'block_count', 'module_count'])],
    ['函数数量', getMetric(repo, ['function_count', 'functions'])],
    ['置信度', getMetric(repo, ['confidence', 'comparison_confidence'])]
  ];
  return (
    <section className="identity-card">
      <div className="identity-card__head">
        <div>
          <p className="eyebrow">Repository Identity</p>
          <h1>{getRepoName(repo)}</h1>
        </div>
        <div className="identity-card__score">
          <strong>{score === undefined ? '暂无评分' : `${score} / 100`}</strong>
          <ScoreBadge level={getLevel(repo)} />
        </div>
      </div>
      <div className="field-grid">
        {fields.map(([label, value]) => <div key={label}><span>{label}</span><strong>{value}</strong></div>)}
      </div>
      {url !== '暂无数据' ? (
        <a className="link-row" href={url} target="_blank" rel="noreferrer">
          <ExternalLink size={16} />
          <span>{url}</span>
        </a>
      ) : null}
    </section>
  );
}
