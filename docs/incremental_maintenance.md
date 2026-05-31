# 增量维护工作流

目标：让内容提炼方案从“一次性项目”变成“可持续维护的流水线”。

适用前提：
- 原始语料持续沉淀在 `docs/<corpus>/`
- 自动产物由脚本生成
- 长期文档由人工确认后维护

---

## 1. 目录分工

### 1.1 原始语料

- `docs/<corpus>/`
- 只放原始文章，原则上只增不删
- 如果原文需要修正，尽量保留文件名稳定，避免影响增量识别

### 1.2 自动产物

- `outputs/<corpus>/`
- 由脚本自动刷新：
  - `content_index.jsonl`
  - `claim_candidates.jsonl`
  - `holdout_list.md`
  - `corpus_summary.json`

### 1.3 状态文件

- `outputs/<corpus>/state/`
- 用于判断“本轮新增了什么、更新了什么、该复核什么”：
  - `manifest.json`
  - `review_queue.md`
  - `changelog.md`

### 1.4 人工策展文档

- `outputs/<corpus>/`
- 这些文件不应被脚本整篇覆盖：
  - `taxonomy.md`
  - `beliefs_models.md`
  - `style_dna.md`（仅 `AUTO` 区块允许脚本同步）
  - `style_spec.md`
  - `validation_report.md`

---

## 2. 日常更新流程

### 2.1 新增文章

把新文章放入：

```text
docs/<corpus>/
```

要求：
- 尽量保持 Markdown 格式稳定
- 标题、发布时间、原文链接优先放在现有元数据格式里
- 运行脚本时会检查“新增/更新文章标题是否与现有语料重复”；若重复（含常见复制后缀，如 ` 1`、`(1)`、`（1）`、`副本`），脚本会直接中止，需先清理重复文件

### 2.2 运行增量提取

命令：

```bash
python3 scripts/zhuama_extract.py --corpus zhuama
```

如果未来新增其他账号语料：

```bash
python3 scripts/zhuama_extract.py --corpus <corpus_name>
```

### 2.3 查看本轮复核队列

重点先看：

```text
outputs/<corpus>/state/review_queue.md
```

这个文件会告诉你：
- 本轮新增几篇
- 哪些文章被识别为更新
- 主题分布是否变化
- 关键 A 类指标是否漂移
- 建议优先复核哪些长期文档

---

## 3. 三类更新节奏

### 3.1 轻更新

适用：
- 新增 1-5 篇文章
- 主题结构没有明显变化
- 只想同步自动统计和候选证据

动作：
- 跑脚本
- 查看 `review_queue.md`
- 如有必要，仅更新：
  - `style_dna.md` 中 A 类统计
  - 典型样本候选
  - `beliefs_models.md` 的证据补充

### 3.2 月度重更新

适用：
- 累计新增语料达到现有总量的 10%-20%
- 某个主题新增过多，可能改变风格基线
- holdout 清单发生变化

动作：
- 跑脚本
- 复核：
  - `taxonomy.md`
  - `beliefs_models.md`
  - `style_dna.md`
  - `style_spec.md`
  - `validation_report.md`
- 至少补 1 次 holdout 复测

### 3.3 框架级更新

适用：
- 方法论本身发生变化
- 例如文风框架从旧结构升级到新 8 层结构

动作：
- 优先更新：
  - `docs/methodology.md`
  - `templates/prompts.md`
  - `templates/rubric.md`
  - `content-distill` skill
- 这类更新不要和日常增量混在同一轮完成

---

## 4. 状态文件说明

### 4.1 `manifest.json`

作用：
- 为每篇文章分配稳定 `content_id`
- 记录 `file_hash`
- 识别 `new / updated / unchanged`
- 记录当前属于 `train` 还是 `holdout`

适合做：
- 增量识别
- 后续引用稳定文章编号
- 为 review queue 提供数据来源

### 4.2 `review_queue.md`

作用：
- 把本轮变更翻译成“人工下一步要做什么”

适合先看：
- 新增/更新文章清单
- 指标变化
- 建议复核文档

### 4.3 `changelog.md`

作用：
- 记录每次运行脚本后的总体变化
- 帮助回溯“什么时候新增了哪批文章”

注意：
- 它是运行日志，不是最终知识文档

---

## 5. 长期文档怎么同步最稳

原则：
- 自动层负责发现变化
- 人工层负责批准更新

建议规则：

- `taxonomy.md`
  - 只有出现新主题或原主题权重明显变化时再改

- `beliefs_models.md`
  - 只在新文章补充了关键证据、边界或反例时改

- `style_dna.md`
  - A 类统计可以更频繁更新
  - B/C/D 只在足够证据支持下再改

- `style_spec.md`
  - 只有当风格执行规则真的发生变化时才改
  - 不要因为新增 1 篇文章就频繁调整写作约束

- `validation_report.md`
  - 建议每月重更新时补一次复测

---

## 6. 推荐操作顺序

每次新增文章后，按这个顺序做：

1. 放入新文章到 `docs/<corpus>/`
2. 运行提取脚本
3. 打开 `state/review_queue.md`
4. 先确认新文章的元数据和主题归类
5. 再决定是否需要修改长期文档
6. 如需修改，优先补证据与统计，再改结论
7. 月度时补 `validation_report.md`

---

## 7. 当前脚本入口

现已支持：

```bash
python3 scripts/zhuama_extract.py --corpus zhuama
```

当前已具备：
- 稳定 `content_id`
- `new / updated / unchanged` 增量识别
- `manifest.json`
- `review_queue.md`
- `changelog.md`
- 自动刷新索引、claims、holdout、summary
- 自动同步 `style_dna.md` 中已标记的 `AUTO` 区块（当前覆盖顶部语料摘要，以及标题/开头/结构/句法/词汇/观点/案例/情绪 8 个 A 类区块）

下一步可继续增强：
- 单独生成“典型样本候选”
- 自动输出“哪些模型需要复测”
