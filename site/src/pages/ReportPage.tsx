import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { loadReports } from '../lib/api';
import { encodedName, extractReportOverview, truncateMarkdown } from '../lib/utils';
import { LoadingState } from '../components/common/LoadingState';
import { ReportTabs } from '../components/workspace/ReportTabs';

export function ReportPage() {
  const params = useParams();
  const repoName = params.repoName ? decodeURIComponent(params.repoName) : '';
  const [loading, setLoading] = useState(true);
  const [reports, setReports] = useState({ description: '', final: '' });

  useEffect(() => {
    let alive = true;
    loadReports(repoName).then((content) => {
      if (alive) {
        setReports(content);
        setLoading(false);
      }
    });
    return () => { alive = false; };
  }, [repoName]);

  const overview = useMemo(() => {
    const finalOverview = extractReportOverview(reports.final);
    if (finalOverview) return finalOverview;
    const descriptionOverview = extractReportOverview(reports.description);
    if (descriptionOverview) return descriptionOverview;
    if (reports.final.trim()) return truncateMarkdown(reports.final) || '暂无项目描述';
    if (reports.description.trim()) return truncateMarkdown(reports.description) || '暂无项目描述';
    return '暂无项目描述';
  }, [reports]);

  if (loading) return <LoadingState />;

  return (
    <div className="page-stack">
      <section className="page-title">
        <p className="eyebrow">Report</p>
        <h1>{repoName}</h1>
        <p>{overview}</p>
        <Link to={`/workspaces/${encodedName(repoName)}`}>返回详情页</Link>
      </section>
      <section className="section-block"><ReportTabs description={reports.description} final={reports.final} /></section>
    </div>
  );
}
