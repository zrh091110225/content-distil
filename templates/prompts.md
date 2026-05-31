# Prompt 模板（内容提炼 / 文风 DNA / 双重验证）

使用方式：
- 把 `{{变量}}` 替换为你的真实输入
- 尽量一次只跑一个模板，产物保存后再进入下一个模板
- 默认输出为 Markdown 表格或 YAML，便于人工复核与版本迭代

通用约束（建议每次都带上）：
- 不要编造不存在的证据；每条结论必须给出证据引用（段落原文或链接+段落摘要）
- 出现信息不足时明确标注“未知/推测/置信度”
- 遇到矛盾不强行统一，按时间/场景/核心张力三类记录

---

## 0. 语料归一化与切分

### 0.1 归一化（把原始内容转为统一字段）

输入：
- `{{raw_content}}`：一篇内容（含标题、日期、平台、正文、链接）

Prompt：

```text
你是内容归档助手。请把下面内容归一化为结构化条目，字段必须齐全，并保持原文信息不丢失。

输出格式：YAML（严格按字段输出，不要多余解释）

字段：
- id: 由你生成，格式 C-YYYYMMDD-序号
- title:
- date:
- platform:
- url:
- author_or_account:
- content_type: [文章|口播稿|直播整理|短帖线程|其他]
- body: 正文（保留原段落）
- notes: 你对该内容的简短备注（最多100字）

原始内容：
{{raw_content}}
```

### 0.2 切分为证据单元（段落/语义块）

输入：
- `{{body}}`：正文

Prompt：

```text
你是内容切分助手。请把正文切分为“证据最小单元”，每个单元是一个自然段或2-4句的语义块。

要求：
- 不要改写原文，只做切分与编号
- 若原文段落过长，可按语义切分为多个块

输出格式：Markdown 表格
列：
- evidence_id: E-序号（从001开始）
- excerpt: 原文摘录
- context: 该段在讨论什么问题（不超过30字）

正文：
{{body}}
```

---

## 1. 证据卡片 → 观点卡片

### 1.1 从证据抽取观点（Claim Card）

输入：
- `{{evidence_table}}`：上一步输出的证据表

Prompt：

```text
你是观点抽取助手。请基于证据表，为每条证据提炼“可被反驳的主张句”，并按类型归类。

约束：
- 主张句必须能被反驳（避免空泛正确）
- 每条主张必须引用 evidence_id
- 必须给出至少1条边界/反例（可来自同文其他段落；若没有，标注“待补证据”）

输出格式：Markdown 表格
列：
- claim_id: CL-序号（从001开始）
- claim: 主张句
- type: [事实判断|价值判断|策略判断]
- triggers: 触发条件/适用情境（<=30字）
- evidence: 支撑证据（evidence_id列表）
- boundary_or_counterexample: 边界/反例（<=50字，若无写“待补证据”）

证据表：
{{evidence_table}}
```

### 1.2 合并同义观点（去重与归并）

输入：
- `{{claims_table}}`

Prompt：

```text
你是观点去重助手。请对观点表做归并，合并同义或高度重叠的观点，保留最清晰、最可被反驳的表述。

输出：
1) 合并后的观点表（同样字段）
2) 归并映射表：原claim_id -> 新claim_id

观点表：
{{claims_table}}
```

---

## 2. 领域地图（Domain Map）与概念口径（Concept Lexicon）

### 2.1 生成主题 Taxonomy（先宽后窄）

输入：
- `{{content_list}}`：多篇内容的标题+摘要（或直接给多篇正文）

Prompt：

```text
你是领域建模助手。请从该账号内容中提炼一个可持续维护的主题 taxonomy（2-3层）。

要求：
- 先给“候选主题集合（较宽）”，再收敛为“稳定taxonomy”
- 每个叶子主题给3个典型问题（读者会问的问题）
- 避免空泛词（如“方法论”“思考”），尽量使用领域内可操作名词

输出格式：YAML

输入内容：
{{content_list}}
```

### 2.2 抽取高频概念并写“账号口径定义”

输入：
- `{{evidence_table}}` 或 `{{claims_table}}`

Prompt：

```text
你是概念口径助手。请抽取该账号的高频概念（含术语、指标、框架名），并为每个概念写“账号口径定义”。

要求：
- 定义要贴近账号表达，不要写百科定义
- 给出同义/近义概念边界
- 给出常用类比（如果账号习惯类比）
- 给出常见误用与纠偏句式（如果能从证据推断）
- 每条概念至少引用1条 evidence_id 或 claim_id

输出格式：Markdown 表格
列：
- concept
- account_definition
- boundaries (synonyms/nearby/opposites)
- typical_analogy
- common_misuse_and_fix
- evidence

输入：
{{claims_table}}
```

---

## 3. 理念/偏好/立场（Beliefs & Preferences）

### 3.1 提炼核心信念与反对清单

输入：
- `{{claims_table}}`

Prompt：

```text
你是理念提炼助手。请把该账号的长期观点抽象为“核心信念/反对清单”，并标注置信度与证据。

输出格式：YAML
字段：
- beliefs:
  - belief:
    type: [价值观|世界观假设|长期策略]
    confidence: [高|中|低]
    evidence: [claim_id...]
    boundary: 边界/例外
- anti_beliefs:
  - anti_belief:
    confidence:
    evidence:
    why_it_matters: 为什么这是红线
- audience_assumptions:
  - assumption:
    evidence:

观点表：
{{claims_table}}
```

### 3.2 构建偏好矩阵（取舍维度与阈值条件）

输入：
- `{{claims_table}}`

Prompt：

```text
你是偏好建模助手。请识别该账号在讨论中经常出现的“权衡维度”，并构建偏好矩阵。

要求：
- 每个维度必须给出“账号更偏向哪一端”与“阈值条件/例外”
- 每个维度至少引用2条证据（claim_id或evidence_id）

输出格式：Markdown 表格
列：
- tradeoff_dimension (A vs B)
- default_preference (偏向A或偏向B)
- threshold_conditions (何时反转)
- evidence

观点表：
{{claims_table}}
```

---

## 4. 心智模型提炼（Model Cards）

### 4.1 生成模型候选（先多后少）

输入：
- `{{claims_table}}`

Prompt：

```text
你是心智模型提炼助手。请从观点表中提炼“模型候选列表”（建议8-12个），每个候选都要可运行，而不是口号。

输出格式：Markdown 表格
列：
- candidate_model
- one_sentence_definition
- variables_and_relation
- triggers
- evidence (claim_id列表)
- why_it_might_be_unique

观点表：
{{claims_table}}
```

### 4.2 三重验证与降级（收敛到3-7个模型）

输入：
- `{{candidate_models_table}}`
- `{{holdout_snippets}}`：验证集里3-5个“新问题/新情境”描述（用账号受众会问的方式写）

Prompt：

```text
你是模型验证助手。请对每个模型候选进行三重验证，并按规则收敛为最终模型集（3-7个）。

三重验证：
1) 跨主题复现：是否在至少2个不同子议题出现（用证据说明）
2) 有生成力：能否对验证集新问题给出推断与推理链
3) 有排他性：是否体现独特视角（与行业共识/泛泛建议可区分）

降级规则：
- 通过2-3项 -> 心智模型
- 通过1项 -> 决策启发式
- 通过0项 -> 情境性表达（不纳入）

输出格式：YAML
字段：
- mental_models: [Model Card...]
- heuristics: [Heuristic Card...]
- discarded: [Discarded...]

Model Card字段：
- name
- definition
- variables_and_relation
- triggers
- inference_rules (步骤或If/Then)
- evidence (claim_id或evidence_id，至少3条)
- boundaries_and_failure_modes
- counterexamples
- validation:
  - cross_topic_recurrence: [pass|fail] + why
  - generative_power: [pass|fail] + example_inference
  - exclusivity: [pass|fail] + why

输入：
候选模型：
{{candidate_models_table}}

验证集新问题：
{{holdout_snippets}}
```

---

## 5. 文风 DNA 提取（Style DNA）

### 5.1 从样本段落统计“句式指纹”

输入：
- `{{sample_paragraphs}}`：不少于20段原文段落

Prompt：

```text
你是文风分析助手。请对样本段落做“句式指纹”统计与总结。

要求：
- 先给出“可测指标”的统计结果（均值 + 区间，优先给P25-P75）
- 再给出“写作约束”（哪些必须命中，哪些可容忍偏离）
- 同时抽取代表性例句（每项2-3句），用于人工校准

输出格式：Markdown
包含：
1) 指标表（指标名/均值/区间/必须或可容忍/备注）
2) 风格标签（正式↔口语等）
3) 代表性例句（按指标归类）

样本段落：
{{sample_paragraphs}}
```

### 5.2 提取结构习惯与段落节奏（写作模板）

输入：
- `{{sample_articles}}`：至少5篇原文（全文或结构摘要）

Prompt：

```text
你是结构分析助手。请提炼该账号的写作结构习惯与段落节奏，输出可直接复用的“结构模板库”。

要求：
- 至少输出3个模板
- 每个模板必须给：适用场景、段落骨架、常用句式/连接词、典型例子引用

输出格式：Markdown

原文样本：
{{sample_articles}}
```

### 5.3 词汇与修辞：关键词/禁忌词/口癖

输入：
- `{{sample_paragraphs}}`

Prompt：

```text
你是词汇分析助手。请提取该账号的词汇与修辞特征。

输出格式：YAML
字段：
- keywords: 高频词与固定搭配（给出解释与证据）
- taboo_words: 禁忌词（几乎不用/刻意避免；若不确定标注低置信度）
- catchphrases: 口癖/高频短语（建议使用频率与场景）
- emotional_tone: 情绪色彩画像（冷静/鼓励/警告/讽刺等）
- evidence: 每项至少给1条引用（段落摘录或evidence_id）

样本段落：
{{sample_paragraphs}}
```

### 5.4 B类半量化判定（8层 1-5分）

输入：
- `{{sample_articles}}`：建议 3-8 篇原文
- `{{style_dna}}`：当前版本的文风 DNA 文档

Prompt：

```text
你是文风半量化判定助手。请基于样本文本和既有的 style_dna 文档，对该账号做 8 层 B 类半量化评分。

目标：
- 不是给“整体像不像”的总印象
- 而是按 8 层逐项评分，并给出证据和解释

评分规则：
- 统一使用 1-5 分
- 1 分 = 几乎没有该特征，或明显不像
- 3 分 = 基本命中，能看出该层风格，但辨识度一般
- 5 分 = 高度稳定、辨识度强，接近账号稳定气质
- 2 分和 4 分用于相邻档位之间的过渡

硬约束：
- 不要编造不存在的特征
- 每个分数都必须给至少 1 条原文证据
- 如果某项证据不足，明确标注“低置信度”
- 若 A 类统计与 B 类判断冲突，优先指出冲突，不要强行统一

请按以下项目评分：
1. 标题 DNA
- 冲突感
- 反常识度
- 搜索感
- 点击感
- 情绪强度

2. 开头 DNA
- 开头抓力
- 判断强度
- 画面感
- 压迫感
- 进入主题效率

3. 结构 DNA
- 结构清晰度
- 推进感
- 收束力度
- 信息密度平衡度

4. 句法 DNA
- 口语化程度
- 节奏感
- 压迫感
- 权威感

5. 词汇 DNA
- 术语密度
- 口语化程度
- AI味程度
- 官话感

6. 观点 DNA
- 观点强度
- 反常识程度
- 抽象层级
- 确定感
- 说教感

7. 案例 DNA
- 案例具体度
- 真实性
- 共鸣度
- 解释力

8. 情绪 DNA
- 情绪强度
- 吐槽浓度
- 焦虑制造程度
- 安抚程度
- 权威感
- 陪伴感
- 战斗感

输出格式：Markdown

先输出一张总表：
- 层
- 维度
- 分数
- 置信度（高/中/低）
- 证据摘要
- 判定理由

然后输出一段“B类总结”：
- 该账号最稳定的 5 个高分特征
- 最容易被误判的 3 个维度
- 与 A 类统计最可能冲突的地方

样本文本：
{{sample_articles}}

style_dna：
{{style_dna}}
```

---

## 6. 文风复刻：同事实改写 / 新问题写作

### 6.1 同事实改写（保持信息不变，只调文风）

输入：
- `{{source_text}}`：一段中性说明或你自己的草稿
- `{{style_dna}}`：上一步得到的文风 DNA 要点

Prompt：

```text
你是该账号的写作替身。请在不改变事实与逻辑的前提下，把下面文本改写为符合该账号文风的版本。

硬约束：
- 保持事实不变，不添加新信息
- 遵守禁忌词（taboo_words）=0违例
- 使用结构模板（从style_dna中选择最匹配的一个并注明）
- 口癖适度使用，不超过每500字2次
- 先做 D 类禁忌检查：标题、开头、结构、句法、词汇、观点、案例、情绪 8 层都不能出现明显违例

输出：
1) 改写后的文本
2) 自检清单（逐项说明是否满足：句长/语气/结构/关键词/禁忌词）
3) D类违例检查（8层逐项写“0/1 + 一句原因”）

文风DNA：
{{style_dna}}

原文本：
{{source_text}}
```

### 6.2 新问题写作（验证“模型生成力 + 文风一致”）

输入：
- `{{new_question}}`：验证集中的新问题
- `{{mental_models}}`：最终模型卡片
- `{{style_dna}}`

Prompt：

```text
你是该账号的写作者。请针对新问题写一篇短文（{{length_hint}}），必须同时满足：
- 内容：明确指出你使用了哪些心智模型（至少1个），并在文末给出“推理链摘要”
- 文风：遵守style_dna的关键约束（结构模板、句式指纹、关键词与禁忌词）
- 生成前先检查 D 类禁忌，确保 8 层都不触发明显违例

输出：
1) 正文
2) 使用的模型：模型名列表
3) 推理链摘要（不超过150字）
4) 文风自检结果（按必须命中项逐条写）
5) D类违例检查（8层逐项写“0/1 + 一句原因”）

新问题：
{{new_question}}

心智模型：
{{mental_models}}

文风DNA：
{{style_dna}}
```

---

## 7. 双重验证模板

### 7.1 量化验证（指标命中表）

输入：
- `{{style_dna_metrics}}`：指标基线区间（均值/P25-P75/阈值）
- `{{generated_text}}`：复刻文本

Prompt：

```text
你是文风质检助手。请对复刻文本做“量化验证”，输出指标命中表。

要求：
- 计算/估算：平均句长、短句比例、疑问句比例、转折频率、因果连接、第一人称比例
- 输出每项：基线区间、复刻值、是否命中、偏差原因、修订建议
- 额外检查：禁忌词违例（必须为0）

输出格式：Markdown 表格

基线指标：
{{style_dna_metrics}}

复刻文本：
{{generated_text}}
```

### 7.2 人工盲测脚本（A/B 对照）

输入：
- `{{original_excerpt}}`：原文段落（选与主题相近的一段）
- `{{generated_excerpt}}`：复刻段落

Prompt：

```text
你是盲测组织者。请把两段文字改写成盲测问卷格式，不暴露哪段是原文。

输出：
1) A段/B段（随机顺序）
2) 评分表（0-5分）：像不像该账号（整体）、结构、语气、用词、节奏
3) 对照清单（是/否）：是否出现禁忌词、是否概念口径一致、是否有典型反例/提醒方式
4) 评语栏（开放题）

原文：
{{original_excerpt}}

复刻：
{{generated_excerpt}}
```
