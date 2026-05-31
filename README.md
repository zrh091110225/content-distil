# content-distil 项目使用说明

本项目用于把一组同账号/同作者语料提炼成可复用的内容系统与文风系统。当前仓库以 `zhuama` 语料为示例，已经沉淀了自动提取脚本、方法论文档、Prompt/Rubric 模板，以及一组已生成的分析产物。

核心目标不是做文章摘要，而是形成可验证、可维护、可复刻的账号级资料：

- 领域结构：这个账号长期讲什么、如何分层。
- 观点系统：它相信什么、反对什么、如何权衡。
- 心智模型：遇到新问题时，它会怎样判断。
- 文风 DNA：标题、开头、结构、句法、词汇、观点、案例、情绪 8 层风格基线。
- 执行规范：把分析结果转成可直接用于写作/改写的 style spec。
- 验证机制：使用 holdout、量化指标和盲测记录验证“像不像”和“能不能用”。

---

## 1. 目录结构

```text
content-distil/
├── docs/
│   ├── methodology.md                 # 内容提炼方法论
│   ├── incremental_maintenance.md     # 增量维护流程
│   └── zhuama -> .../raw/import       # 当前语料目录，使用符号链接
├── scripts/
│   └── zhuama_extract.py              # 自动提取、统计、增量维护脚本
├── templates/
│   ├── prompts.md                     # LLM 提炼 Prompt 模板
│   ├── rubric.md                      # 验收评分表
│   └── worksheet.md                   # 人工复核工作表
└── outputs/
    └── zhuama/
        ├── content_index.jsonl        # 全量语料索引与清洗正文
        ├── claim_candidates.jsonl     # 观点候选
        ├── corpus_summary.json        # 训练集统计摘要
        ├── holdout_list.md            # 验证集清单
        ├── taxonomy.md                # 领域地图
        ├── beliefs_models.md          # 信念、偏好、心智模型
        ├── style_dna.md               # 文风 DNA 分析版
        ├── style_spec.md              # 文风执行版
        ├── validation_report.md       # holdout 验证记录
        ├── generated/                 # 自动生成的候选材料
        └── state/                     # 增量维护状态文件
```

当前 `docs/zhuama` 是一个符号链接，指向本机原始语料目录：

```text
/Users/hymanhai/obsidiandb/raw/import
```

因此，在另一台机器上使用本项目时，需要重新准备 `docs/<corpus>/` 语料目录，或重建对应符号链接。

---

## 2. 运行环境

脚本只依赖 Python 标准库，无需安装第三方包。

建议环境：

```bash
python3 --version
```

推荐使用 Python 3.10+。

查看脚本参数：

```bash
python3 scripts/zhuama_extract.py --help
```

---

## 3. 准备语料

默认语料位置：

```text
docs/<corpus>/
```

当前默认 corpus 是：

```text
docs/zhuama/
```

每篇文章建议保存为一个 Markdown 文件，尽量包含以下信息：

```markdown
# 文章标题

> 公众号：账号名
> 发布时间：2026-01-01 12:00:00
> 原文链接：https://example.com/article

正文内容……
```

脚本会自动处理：

- frontmatter
- 微信导航噪音
- 图片行
- 引用元数据
- 部分活动/票务噪音
- 标题、发布时间、链接等基础元数据

脚本还会在增量运行时检查新增/更新文章是否与现有语料标题重复。常见的复制后缀也会被识别为重复，例如 ` 1`、`(1)`、`（1）`、`副本`。一旦命中，脚本会中止，避免把重复文章写进语料库。

文件名会参与主题粗分类。当前脚本对 `zhuama` 语料内置了部分关键词规则，例如：

- `旅途`
- `牺牲`
- `工作坊`
- `招募`
- `回顾`
- `开票`
- `观后感`

如果新增账号或新主题，可能需要调整 `scripts/zhuama_extract.py` 里的 `topic_from_filename()`。

---

## 4. 一键生成/刷新产物

默认运行：

```bash
python3 scripts/zhuama_extract.py --corpus zhuama
```

等价于读取：

```text
docs/zhuama/
```

并输出到：

```text
outputs/zhuama/
```

如果要处理另一个语料集：

```bash
python3 scripts/zhuama_extract.py --corpus <corpus_name>
```

如果语料目录和输出目录不按默认结构放置：

```bash
python3 scripts/zhuama_extract.py \
  --corpus zhuama \
  --docs-dir /path/to/docs \
  --out-dir /path/to/outputs
```

调整验证集比例：

```bash
python3 scripts/zhuama_extract.py --corpus zhuama --holdout-ratio 0.2
```

默认验证集比例是 `0.2`，即按主题分层抽取约 20% 作为 holdout。

---

## 5. 脚本会生成什么

每次运行脚本后，会刷新以下自动产物：

| 文件 | 用途 |
|---|---|
| `outputs/<corpus>/content_index.jsonl` | 全量文章索引，含清洗后的正文、元数据、主题、状态 |
| `outputs/<corpus>/claim_candidates.jsonl` | 从训练集提取的观点候选段落 |
| `outputs/<corpus>/holdout_list.md` | 按主题分层抽样的验证集清单 |
| `outputs/<corpus>/corpus_summary.json` | 标题、开头、结构、句法、词汇、案例、情绪等 A 类统计 |
| `outputs/<corpus>/state/manifest.json` | 每篇文章的稳定 ID、hash、split、增量状态 |
| `outputs/<corpus>/state/review_queue.md` | 本轮新增/更新、指标漂移、建议复核动作 |
| `outputs/<corpus>/state/changelog.md` | 每次运行的增量日志 |
| `outputs/<corpus>/generated/typical_sample_candidates.md` | 8 层文风典型样本候选 |
| `outputs/<corpus>/generated/model_retest_candidates.md` | 心智模型复测候选 |

此外，脚本会同步更新 `style_dna.md` 中带有 `AUTO` 标记的区块。不要手动删除这些标记，否则自动同步会失效。

---

## 6. 推荐日常工作流

### 6.1 新增文章

把新的 Markdown 文章放入：

```text
docs/<corpus>/
```

然后运行：

```bash
python3 scripts/zhuama_extract.py --corpus <corpus>
```

### 6.2 查看复核队列

优先打开：

```text
outputs/<corpus>/state/review_queue.md
```

重点看：

- 本轮新增了哪些文章
- 哪些文章被识别为更新
- 主题分布是否变化
- 关键 A 类指标是否漂移
- 哪些长期文档建议人工复核

### 6.3 复核自动候选

再看：

```text
outputs/<corpus>/generated/typical_sample_candidates.md
outputs/<corpus>/generated/model_retest_candidates.md
```

用途：

- 从典型样本候选中挑选段落，补进 `style_dna.md`。
- 从模型复测候选中挑 2-3 篇，补进 `validation_report.md`。

### 6.4 更新人工策展文档

以下文件不应被脚本整篇覆盖，需要人工判断后维护：

```text
outputs/<corpus>/taxonomy.md
outputs/<corpus>/beliefs_models.md
outputs/<corpus>/style_dna.md
outputs/<corpus>/style_spec.md
outputs/<corpus>/validation_report.md
```

建议规则：

- 少量新增文章：优先只补证据、典型样本和 A 类统计。
- 主题明显变化：复核 `taxonomy.md`。
- 新文章提供边界/反例：复核 `beliefs_models.md`。
- 风格指标漂移：复核 `style_dna.md` 和 `style_spec.md`。
- holdout 变化：复核 `validation_report.md`。

---

## 7. 如何使用现有分析结果写作

如果目标是“写一篇像该账号的新稿”，推荐阅读顺序：

1. `outputs/<corpus>/style_spec.md`
2. `outputs/<corpus>/beliefs_models.md`
3. `outputs/<corpus>/style_dna.md`

写作时优先使用 `style_spec.md`，它是执行版，已经把分析结果转成可操作规则。

当前 `zhuama` 的执行版要求重点命中：

- 对象/场景先行
- 至少一次问题重定义
- 案例服务观点
- 先托住再推进
- 结尾回到判断、邀请或同行式收束
- 禁止宏大空词、咨询味黑话、廉价恐吓、纯方法清单、高位说教

写完后，建议按以下顺序自检：

1. 先查 D 类禁忌是否为 0。
2. 再查结构模板是否命中。
3. 再查观点是否完成重定义。
4. 再查案例是否具体且服务观点。
5. 最后查句长、转折、问句、人称、类比等量化指标。

---

## 8. 如何新增一个账号/语料集

假设新账号名为 `example`：

1. 新建语料目录：

```bash
mkdir -p docs/example
```

2. 放入 Markdown 文章。

3. 运行脚本：

```bash
python3 scripts/zhuama_extract.py --corpus example
```

4. 检查自动产物：

```text
outputs/example/content_index.jsonl
outputs/example/corpus_summary.json
outputs/example/state/review_queue.md
```

5. 根据新账号特点，人工创建或改写：

```text
outputs/example/taxonomy.md
outputs/example/beliefs_models.md
outputs/example/style_dna.md
outputs/example/style_spec.md
outputs/example/validation_report.md
```

注意：当前脚本文件名仍叫 `zhuama_extract.py`，但参数层面已支持 `--corpus <name>`。如果长期支持多个账号，建议后续把脚本重命名为更通用的 `content_extract.py`，并将主题识别规则配置化。

---

## 9. 常见问题

### 9.1 运行后文章数变成 0

先检查语料目录是否存在：

```bash
ls -la docs/<corpus>
```

如果 `docs/<corpus>` 是符号链接，确认目标目录还存在。

### 9.2 新文章没有正确识别标题/日期

检查 Markdown 顶部是否符合推荐格式：

```markdown
# 标题
> 公众号：账号名
> 发布时间：YYYY-MM-DD HH:MM:SS
> 原文链接：https://...
```

如果没有这些字段，脚本会尽量用文件名和默认账号补齐，但准确性会下降。

### 9.3 主题分类不准

当前主题分类主要依赖文件名关键词。需要修改：

```text
scripts/zhuama_extract.py
```

重点函数：

```python
topic_from_filename()
```

### 9.4 为什么不要直接改自动产物

以下文件每次运行都会被刷新，不适合手工长期维护：

```text
content_index.jsonl
claim_candidates.jsonl
holdout_list.md
corpus_summary.json
state/manifest.json
state/review_queue.md
generated/*.md
```

长期结论应沉淀到：

```text
taxonomy.md
beliefs_models.md
style_dna.md
style_spec.md
validation_report.md
```

### 9.5 什么时候需要完整重做一轮

出现以下情况时，建议做月度/阶段性重更新：

- 新增语料达到现有总量的 10%-20%。
- 新主题大量出现。
- holdout 清单发生明显变化。
- 关键风格指标出现漂移。
- 需要把方法论升级到新的分析框架。

---

## 10. 推荐阅读顺序

如果是第一次接手项目，建议按这个顺序看：

1. `README.md`
2. `docs/methodology.md`
3. `docs/incremental_maintenance.md`
4. `outputs/zhuama/state/review_queue.md`
5. `outputs/zhuama/style_spec.md`
6. `outputs/zhuama/style_dna.md`
7. `outputs/zhuama/beliefs_models.md`
8. `templates/prompts.md`
9. `templates/rubric.md`

如果只是想跑脚本：

```bash
python3 scripts/zhuama_extract.py --corpus zhuama
```

如果只是想用分析结果辅助写作：

```text
先读 outputs/zhuama/style_spec.md，再用 outputs/zhuama/beliefs_models.md 校正判断方式。
```
