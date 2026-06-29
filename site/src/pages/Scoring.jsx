const dimensions = [
  {
    name: '原创性',
    english: 'Originality',
    meaning: '评价作品是否具备独立设计思路，而不是对历史作品或常见模板的简单重复。',
    basis: ['与历史项目的结构相似度', '核心模块组合是否具有独立特征', '报告中是否存在明确的差异化设计证据'],
    high: '核心架构、模块组合或实现路径与历史项目有清晰差异，并能形成可解释的创新证据。',
    low: '与多个历史项目高度相似，核心设计缺少独立判断或明显复用痕迹较重。',
  },
  {
    name: '新颖性',
    english: 'Novelty',
    meaning: '评价作品是否采用新的技术路线、功能组合、模块组织或实现方式。',
    basis: ['语言和技术栈选择', '模块画像中的功能亮点', '与历史库检索结果相比的新增能力'],
    high: '技术路线或功能组合有明确新意，能够在历史对比中体现新的实现角度。',
    low: '技术路径常规，模块组合与历史作品重合度高，缺少新功能或新组织方式。',
  },
  {
    name: '可实践性',
    english: 'Practicality',
    meaning: '评价作品是否具备运行、扩展、复用和继续开发的实际价值。',
    basis: ['模块完整度', '系统调用、文件系统、进程管理等功能可用性', '工程结构是否清晰可扩展'],
    high: '关键模块实现较完整，工程结构清楚，具备较强的运行和后续扩展价值。',
    low: '功能覆盖不足，关键模块缺失或完成度低，实际运行与扩展价值有限。',
  },
  {
    name: '技术难度',
    english: 'Difficulty',
    meaning: '评价作品实现所体现的系统复杂度、底层机制覆盖和工程挑战。',
    basis: ['函数数量和调用边数量', '核心模块数量', '结构复杂度', '是否涉及内核关键机制'],
    high: '覆盖多个核心 OS 模块，调用关系较复杂，涉及较多底层机制与系统性设计。',
    low: '模块较少，内部逻辑简单，主要依赖现成框架或外部代码，底层实现挑战较低。',
  },
  {
    name: '完成度',
    english: 'Completion',
    meaning: '评价作品目标功能完成情况、工程成熟度和报告证据完整性。',
    basis: ['模块完成度分布', '核心功能覆盖范围', '代码画像与报告证据是否完整', '与同类历史项目相比的完成情况'],
    high: '模块实现均衡，核心功能较完整，分析证据和报告材料能够支撑评分结论。',
    low: '关键模块缺失或完成度低，整体系统不完整，报告证据不足以支撑较高评分。',
  },
]

const workflow = ['源码结构读取', '模块完整度分析', '历史相似检索', '创新点与相似点对比', '复杂度与完成度判断', '输出五维评分']

export default function Scoring() {
  return <div className="container">
    <div className="page-title">
      <span>Scoring Logic</span>
      <h1>五维评分逻辑</h1>
      <p>评分结果并非单纯由大模型主观生成，而是结合源码结构画像、模块完整度、历史相似项目检索结果、Hybrid 对比证据和最终报告共同形成。</p>
    </div>

    <section className="score-dim-grid">
      {dimensions.map((d) => <div className="glass score-dim" key={d.english}>
        <div className="dim-head"><h2>{d.name}</h2><span>{d.english}</span><b>20 分</b></div>
        <p>{d.meaning}</p>
        <h4>主要依据</h4>
        <ul>{d.basis.map((x) => <li key={x}>{x}</li>)}</ul>
        <div className="high-low">
          <div><b>高分表现</b><span>{d.high}</span></div>
          <div><b>低分表现</b><span>{d.low}</span></div>
        </div>
      </div>)}
    </section>

    <section className="glass panel">
      <h2>评分流程</h2>
      <div className="workflow-row">{workflow.map((x, i) => <div className="workflow-node" key={x}><span>{i + 1}</span><b>{x}</b></div>)}</div>
    </section>
  </div>
}
