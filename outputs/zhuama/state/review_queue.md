# zhuama 增量复核队列

- 生成时间：2026-05-31 14:15:33
- 总文章数：36
- 训练集：27
- 验证集：9
- 新增：0 篇
- 更新：0 篇
- 未变化：36 篇

## 本轮新增/更新文章

- 无新增或变更文章。

## 主题变化

- 主题分布无显著变化。

## 关键指标变化

- 标题长度 P50：21 -> 22
- 开头场景切入率：0.8636 -> 0.7778
- 每千字案例段落数：4.4700 -> 4.7679

## 建议复核文档

- `style_dna.md`：A 类统计和典型样本候选需要复核。
- `style_spec.md`：若标题/开头/案例/观点指标出现漂移，需同步检查执行约束。
- `validation_report.md`：holdout 清单变化，建议补一轮复测。

## 建议动作

- 先查看 `state/manifest.json` 中本轮 `new/updated` 文章，确认元数据与主题归类是否正确。
- 复核 `generated/typical_sample_candidates.md`：从 8 层候选里挑选可补进 `style_dna.md` 的典型样本。
- 复核 `generated/model_retest_candidates.md`：从 holdout 候选里挑 2-3 篇补做模型复测或边界校正。
- 若只新增少量文章，可先更新 `style_dna.md` 的 A 类统计和典型样本候选，不急于改动 B/C/D。
- 若主题分布或 holdout 发生变化，优先补 `validation_report.md` 的复测记录。
- 当新增文章累计超过现有语料的 10%-20% 时，建议做一次完整月度重更新。
