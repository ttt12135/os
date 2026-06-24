# 历史知识库统计报告

生成时间：2026-06-23 14:02:31
输入文件：`history_knowledge_base/history_profiles_full.json`

---

## 1. 历史库概览

- 历史项目数量：`8`
- 平均函数数量：`20.00`
- 平均调用边数量：`157.38`
- 平均模块数量：`4.88`
- 平均结构复杂度：`0.41`
- 平均模块完整度：`0.36`
- 最大函数数量：`20.00`
- 最大调用边数量：`415.00`
- 最大结构复杂度：`0.50`

## 2. 项目类型分布

| 项目 | 数量 | 占比 |
|---|---:|---:|
| unknown_os_project | 6 | 75.00% |
| basic_kernel | 1 | 12.50% |
| filesystem_focused_project | 1 | 12.50% |

## 3. 语言分布

| 项目 | 数量 | 占比 |
|---|---:|---:|
| rust | 7 | 87.50% |
| c | 1 | 12.50% |

## 4. 核心模块覆盖情况

| 项目 | 数量 | 占比 |
|---|---:|---:|
| process | 6 | 17.65% |
| filesystem | 4 | 11.76% |
| unknown | 4 | 11.76% |
| memory | 4 | 11.76% |
| scheduler | 3 | 8.82% |
| interrupt | 3 | 8.82% |
| syscall | 3 | 8.82% |
| boot | 3 | 8.82% |
| process/syscall | 1 | 2.94% |
| driver | 1 | 2.94% |
| build | 1 | 2.94% |
| user | 1 | 2.94% |

## 5. 函数数量排名

| 排名 | 仓库名 | 函数数量 | 项目类型 | 核心模块 |
|---:|---|---:|---|---|
| 1 | jilindaxue | 20.00 | unknown_os_project | filesystem、process、unknown、scheduler、interrupt |
| 2 | nankai | 20.00 | unknown_os_project | syscall、process、process/syscall、interrupt |
| 3 | qinghuadaxue | 20.00 | unknown_os_project | boot、filesystem、process、memory、scheduler |
| 4 | tianjindaxue | 20.00 | basic_kernel | process、syscall、memory、unknown、driver |
| 5 | tianjingongye | 20.00 | unknown_os_project | boot、filesystem、interrupt、memory、unknown |
| 6 | tongjidaxue | 20.00 | unknown_os_project | process |
| 7 | yanshandaxue | 20.00 | unknown_os_project | boot、memory、process、unknown、scheduler |
| 8 | zhengzhoudaxue111 | 20.00 | filesystem_focused_project | syscall、filesystem、build、user |

## 6. 调用边数量排名

| 排名 | 仓库名 | 调用边数量 | 项目类型 | 核心模块 |
|---:|---|---:|---|---|
| 1 | zhengzhoudaxue111 | 415.00 | filesystem_focused_project | syscall、filesystem、build、user |
| 2 | tianjindaxue | 230.00 | basic_kernel | process、syscall、memory、unknown、driver |
| 3 | tongjidaxue | 138.00 | unknown_os_project | process |
| 4 | qinghuadaxue | 119.00 | unknown_os_project | boot、filesystem、process、memory、scheduler |
| 5 | tianjingongye | 116.00 | unknown_os_project | boot、filesystem、interrupt、memory、unknown |
| 6 | nankai | 107.00 | unknown_os_project | syscall、process、process/syscall、interrupt |
| 7 | yanshandaxue | 92.00 | unknown_os_project | boot、memory、process、unknown、scheduler |
| 8 | jilindaxue | 42.00 | unknown_os_project | filesystem、process、unknown、scheduler、interrupt |

## 7. 结构复杂度排名

| 排名 | 仓库名 | 结构复杂度 | 项目类型 | 核心模块 |
|---:|---|---:|---|---|
| 1 | tianjindaxue | 0.50 | basic_kernel | process、syscall、memory、unknown、driver |
| 2 | zhengzhoudaxue111 | 0.45 | filesystem_focused_project | syscall、filesystem、build、user |
| 3 | qinghuadaxue | 0.43 | unknown_os_project | boot、filesystem、process、memory、scheduler |
| 4 | tianjingongye | 0.43 | unknown_os_project | boot、filesystem、interrupt、memory、unknown |
| 5 | yanshandaxue | 0.43 | unknown_os_project | boot、memory、process、unknown、scheduler |
| 6 | nankai | 0.38 | unknown_os_project | syscall、process、process/syscall、interrupt |
| 7 | jilindaxue | 0.36 | unknown_os_project | filesystem、process、unknown、scheduler、interrupt |
| 8 | tongjidaxue | 0.33 | unknown_os_project | process |

## 8. 模块完整度排名

| 排名 | 仓库名 | 平均模块完整度 | 项目类型 | 核心模块 |
|---:|---|---:|---|---|
| 1 | tongjidaxue | 0.83 | unknown_os_project | process |
| 2 | qinghuadaxue | 0.34 | unknown_os_project | boot、filesystem、process、memory、scheduler |
| 3 | zhengzhoudaxue111 | 0.33 | filesystem_focused_project | syscall、filesystem、build、user |
| 4 | nankai | 0.31 | unknown_os_project | syscall、process、process/syscall、interrupt |
| 5 | tianjingongye | 0.30 | unknown_os_project | boot、filesystem、interrupt、memory、unknown |
| 6 | yanshandaxue | 0.28 | unknown_os_project | boot、memory、process、unknown、scheduler |
| 7 | tianjindaxue | 0.27 | basic_kernel | process、syscall、memory、unknown、driver |
| 8 | jilindaxue | 0.24 | unknown_os_project | filesystem、process、unknown、scheduler、interrupt |

## 9. 历史知识库质量评价

- 当前历史知识库仍处于初步阶段，可以用于流程验证，但相似检索的代表性还有限。
- 从平均函数数量看，历史库项目整体规模偏小，后续应补充更完整的 OS 项目。
- 项目类型覆盖仍不够丰富，后续应补充更多不同方向的历史项目。
- 核心模块覆盖较全面，已包含多类 OS 模块特征。

## 10. 后续建议

- 继续扩充历史 OS 项目数量，优先覆盖不同类型的项目。
- 对历史项目进行统一 full 分析，减少 quick 模式带来的覆盖不足。
- 后续可将 repo_profile_full、module_summary_full 和 final_report 转换为 RAG 文档，增强语义检索能力。
- 可以将该统计报告用于展示系统历史知识库规模与覆盖情况。
