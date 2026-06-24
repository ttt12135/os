# 历史项目批量入库报告

生成时间：2026-06-23 13:52:34

## 1. 基本信息

- 历史项目总目录：`D:\os\history`
- 分析模式：`quick`
- max_blocks：`20`
- 是否启用缓存：`True`
- 是否强制重跑：`False`
- 发现仓库数量：`8`
- 成功数量：`1`
- 跳过数量：`7`
- 失败数量：`0`

## 2. 入库结果

| 序号 | 仓库名 | 状态 | 仓库路径 | 输出 profile | 说明 |
|---:|---|---|---|---|---|
| 1 | jilindaxue | skipped | `D:\os\history\jilindaxue` | `repo_profiles\history\jilindaxue_repo_profile_full.json` | 检测到已有 repo_profile_full，已跳过。 |
| 2 | nankai | skipped | `D:\os\history\nankai` | `repo_profiles\history\nankai_repo_profile_full.json` | 检测到已有 repo_profile_full，已跳过。 |
| 3 | qinghuadaxue | skipped | `D:\os\history\qinghuadaxue` | `repo_profiles\history\qinghuadaxue_repo_profile_full.json` | 检测到已有 repo_profile_full，已跳过。 |
| 4 | tianjindaxue | skipped | `D:\os\history\tianjindaxue` | `repo_profiles\history\tianjindaxue_repo_profile_full.json` | 检测到已有 repo_profile_full，已跳过。 |
| 5 | tianjingongye | skipped | `D:\os\history\tianjingongye` | `repo_profiles\history\tianjingongye_repo_profile_full.json` | 检测到已有 repo_profile_full，已跳过。 |
| 6 | tongjidaxue | skipped | `D:\os\history\tongjidaxue` | `repo_profiles\history\tongjidaxue_repo_profile_full.json` | 检测到已有 repo_profile_full，已跳过。 |
| 7 | yanshandaxue | skipped | `D:\os\history\yanshandaxue` | `repo_profiles\history\yanshandaxue_repo_profile_full.json` | 检测到已有 repo_profile_full，已跳过。 |
| 8 | zhengzhoudaxue111 | success | `D:\os\history\zhengzhoudaxue111` | `repo_profiles\history\zhengzhoudaxue111_repo_profile_full.json` | 入库成功。 |

## 3. 历史知识库输出

- full 历史知识库：`history_knowledge_base\history_profiles_full.json`

## 4. 说明

本报告由 batch_ingest_history 自动生成，用于记录多个历史 OS 项目的入库情况。入库成功的项目会在 repo_profiles/history 目录下生成 repo_profile_full，并被统一汇总进 history_profiles_full.json，供 retrieve_full 阶段进行相似历史项目检索。
