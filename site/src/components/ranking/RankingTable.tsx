import { FileText } from 'lucide-react';
import { Link } from 'react-router-dom';
import { getLevel, getRepoName, getRepoUrl, getSchool, getScore, getStrengths, getTeamName, getWeaknesses, getYear, type RepoRecord } from '../../lib/adapters';
import { encodedName, toDisplay } from '../../lib/utils';
import { ScoreBadge } from '../common/ScoreBadge';

export function RankingTable({ rows }: { rows: RepoRecord[] }) {
  return (
    <>
      <div className="table-wrap desktop-table">
        <table>
          <thead>
            <tr>
              <th>Rank</th>
              <th>队伍编号 / 仓库名</th>
              <th>原始 Fork 地址</th>
              <th>综合评分</th>
              <th>等级</th>
              <th>主要优势</th>
              <th>主要短板</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, index) => {
              const name = getRepoName(row);
              const url = getRepoUrl(row);
              return (
                <tr key={`${name}-${index}`}>
                  <td>#{index + 1}</td>
                  <td><strong>{name}</strong><small>{getTeamName(row)} · {getSchool(row)} · {getYear(row)}</small></td>
                  <td>{url !== '暂无数据' ? <a className="text-link" href={url} target="_blank" rel="noreferrer">{url}</a> : '暂无数据'}</td>
                  <td>{getScore(row) === undefined ? '暂无评分' : `${getScore(row)} / 100`}</td>
                  <td><ScoreBadge level={getLevel(row)} /></td>
                  <td>{toDisplay(getStrengths(row).slice(0, 2))}</td>
                  <td>{toDisplay(getWeaknesses(row).slice(0, 2))}</td>
                  <td><div className="table-actions"><Link to={`/workspaces/${encodedName(name)}`}>详情</Link><Link to={`/reports/${encodedName(name)}`}><FileText size={15} />报告</Link></div></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <div className="mobile-cards">
        {rows.map((row, index) => {
          const name = getRepoName(row);
          return (
            <div className="ranking-card" key={`${name}-mobile-${index}`}>
              <div className="ranking-card__head"><span>Rank #{index + 1}</span><ScoreBadge level={getLevel(row)} /></div>
              <h3>{name}</h3>
              <p>Score: {getScore(row) === undefined ? '暂无评分' : `${getScore(row)} / 100`}</p>
              <p><strong>优势</strong>{toDisplay(getStrengths(row).slice(0, 2))}</p>
              <p><strong>短板</strong>{toDisplay(getWeaknesses(row).slice(0, 2))}</p>
              <div className="button-row"><Link className="button" to={`/workspaces/${encodedName(name)}`}>查看详情</Link><Link className="button button--subtle" to={`/reports/${encodedName(name)}`}>查看报告</Link></div>
            </div>
          );
        })}
      </div>
    </>
  );
}
