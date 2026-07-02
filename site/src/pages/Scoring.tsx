import { useEffect, useState } from 'react';
import { safeFetchJson } from '../lib/api';
import { EmptyState } from '../components/common/EmptyState';

const dimensions = [
  ['原创性', '看是否与历史项目高度相似，是否只是重复已有结构。'],
  ['新颖性', '看模块组合、实现路径、技术选型、设计思路是否有差异。'],
  ['可实践性', '看 README、构建脚本、运行入口、测试、工程结构。'],
  ['技术难度', '看内核模块复杂度、调用关系和系统机制实现深度。'],
  ['完成度', '看核心链路是否闭环，是否存在大量 TODO 或空实现。']
];
const evidence = ['源码结构画像', '函数 / 代码块理解结果', '核心模块覆盖', '历史项目相似度', '工程证据', '风险扣分项'];

export function Scoring() {
  const [logic, setLogic] = useState<Record<string, unknown>>({});
  useEffect(() => { safeFetchJson<Record<string, unknown>>('/data/scoring_logic.json', {}).then(setLogic); }, []);
  return (
    <div className="page-stack">
      <section className="page-title"><p className="eyebrow">Scoring</p><h1>评分方法</h1><p>最终报告、排行榜和前端页面使用同一主评分口径；其他结构分与证据完整度只作为辅助证据。</p></section>
      <section className="dimension-grid">{dimensions.map(([title, text], index) => <div className="section-block" key={title}><span className="step-index">{index + 1}</span><h2>{title}</h2><p>{text}</p></div>)}</section>
      <section className="section-block"><h2>证据来源</h2><div className="evidence-grid">{evidence.map((item) => <div className="evidence-item" key={item}><span>{item}</span><strong>用于支撑评分判断</strong></div>)}</div></section>
      {Object.keys(logic).length ? <section className="section-block"><h2>导出的评分逻辑</h2><pre className="code-panel">{JSON.stringify(logic, null, 2)}</pre></section> : <EmptyState title="暂无评分配置数据" message="如需展示导出的评分规则，请生成 /data/scoring_logic.json。" />}
    </div>
  );
}
