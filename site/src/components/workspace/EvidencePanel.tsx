import { getMetric, type RepoRecord } from '../../lib/adapters';

export function EvidencePanel({ repo, hasFinalReport, hasComparison }: { repo: RepoRecord; hasFinalReport: boolean; hasComparison: boolean }) {
  const rows = [
    ['文件数量', getMetric(repo, ['file_count', 'files_count', 'source_file_count'])],
    ['代码块数量', getMetric(repo, ['code_block_count', 'block_count', 'module_count'])],
    ['函数数量', getMetric(repo, ['function_count', 'functions'])],
    ['调用边数量', getMetric(repo, ['edge_count', 'call_edge_count'])],
    ['核心模块覆盖', getMetric(repo, ['core_modules', 'core_module_coverage'])],
    ['README', getMetric(repo, ['has_readme', 'readme'], '暂无数据')],
    ['构建脚本', getMetric(repo, ['has_build_script', 'build_script', 'build'], '暂无数据')],
    ['最终报告', hasFinalReport ? '已生成' : '暂无数据'],
    ['历史对比结果', hasComparison ? '已生成' : '暂无数据'],
    ['TODO / 空实现风险', getMetric(repo, ['todo_count', 'unimplemented_count', 'risk_count', 'risks'])]
  ];
  return (
    <div className="evidence-grid">
      {rows.map(([label, value]) => (
        <div className="evidence-item" key={label}>
          <span>{label}</span>
          <strong>{value}</strong>
        </div>
      ))}
    </div>
  );
}
