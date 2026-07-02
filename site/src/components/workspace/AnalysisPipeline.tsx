import { StatusBadge } from '../common/StatusBadge';

const labels = ['Imported', 'Parsed', 'Understood', 'Profiled', 'Retrieved', 'Compared', 'Scored', 'Reported'];
const hints = ['repo_sources', 'code_blocks', 'function_analysis', 'repo_profiles', 'comparisons', 'evaluation', 'evaluation', 'reports'];

function inferStatus(repo: Record<string, unknown>, index: number) {
  const key = hints[index];
  const value = repo[key];
  if (value === undefined || value === null) return 'partial';
  if (Array.isArray(value)) return value.length ? 'done' : 'missing';
  if (typeof value === 'object') return Object.keys(value).length ? 'done' : 'missing';
  if (typeof value === 'boolean') return value ? 'done' : 'missing';
  return value ? 'done' : 'partial';
}

export function AnalysisPipeline({ repo, compact = false }: { repo?: Record<string, unknown>; compact?: boolean }) {
  return (
    <div className={compact ? 'pipeline pipeline--compact' : 'pipeline'}>
      {labels.map((label, index) => {
        const status = repo ? inferStatus(repo, index) : 'partial';
        return (
          <div className="pipeline-step" key={label}>
            <span>{index + 1}</span>
            <strong>{label}</strong>
            <StatusBadge status={status} />
          </div>
        );
      })}
    </div>
  );
}
