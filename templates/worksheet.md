# 工作表（可复制粘贴填写）

用途：把提炼过程“落在纸面上”，方便多人协作与复核。建议每轮迭代保留版本（v1/v2/v3），避免在同一份里反复覆盖导致信息丢失。

---

## 1) 语料清单（Content Index）

| content_id | date | platform | title | url | topic_tags(1-3) | notes |
|---|---|---|---|---|---|---|
| C-YYYYMMDD-001 |  |  |  |  |  |  |

---

## 2) 证据卡片（Evidence Cards）

| evidence_id | content_id | excerpt(原文摘录) | context(在讲什么) | initial_tags | link |
|---|---|---|---|---|---|
| E-001 | C-YYYYMMDD-001 |  |  |  |  |

---

## 3) 观点卡片（Claim Cards）

| claim_id | claim(可反驳主张句) | type(事实/价值/策略) | triggers(适用情境) | evidence_ids | boundary_or_counterexample |
|---|---|---|---|---|---|
| CL-001 |  |  |  | E-001,E-014 |  |

---

## 4) 领域地图（Domain Map）

### 4.1 Taxonomy（2-3层）

```yaml
domain_map:
  - domain: {{领域}}
    subtopics:
      - name: {{子议题}}
        typical_questions:
          - {{典型问题1}}
          - {{典型问题2}}
          - {{典型问题3}}
        representative_evidence:
          - E-001
          - E-014
```

### 4.2 概念口径表（Concept Lexicon）

| concept | account_definition(账号口径) | boundaries(同/近/反) | typical_analogy | common_misuse_and_fix | evidence |
|---|---|---|---|---|---|
|  |  |  |  |  | E-001 |

---

## 5) 理念/偏好/立场（Beliefs & Preferences）

### 5.1 核心信念（Beliefs）

| belief | type(价值/世界观/长期策略) | confidence(高/中/低) | evidence | boundary |
|---|---|---|---|---|
|  |  |  | CL-001 |  |

### 5.2 反对清单（Anti-beliefs）

| anti_belief | confidence | evidence | why_it_matters |
|---|---|---|---|
|  |  |  |  |

### 5.3 偏好矩阵（Tradeoffs）

| tradeoff_dimension (A vs B) | default_preference | threshold_conditions | evidence |
|---|---|---|---|
|  |  |  | CL-001,CL-007 |

### 5.4 受众假设（Audience Assumptions）

| assumption | evidence |
|---|---|
|  | E-003 |

---

## 6) 心智模型卡片（Model Cards）

```yaml
mental_models:
  - name: {{模型名（账号口吻）}}
    definition: {{一句话定义}}
    variables_and_relation: {{输入/中介/输出关系}}
    triggers: {{何时使用}}
    inference_rules:
      - {{步骤1}}
      - {{步骤2}}
    evidence:
      - E-001
      - E-014
      - E-078
    boundaries_and_failure_modes:
      - {{失效条件1}}
    counterexamples:
      - {{反例1}}
    validation:
      cross_topic_recurrence: { result: pass, why: {{说明}} }
      generative_power: { result: pass, example_inference: {{用验证集新问题举例}} }
      exclusivity: { result: fail, why: {{说明}} }
```

---

## 7) 文风 DNA（Style DNA）

### 7.1 句式指纹基线（Metrics Baseline）

| metric | mean | P25-P75 | must_hit?(Y/N) | notes |
|---|---:|---:|---|---|
| 平均句长（字/句） |  |  | Y |  |
| 短句比例（<=15字） |  |  | N |  |
| 疑问句比例 |  |  | N |  |
| 转折频率（但是/不过/然而） |  |  | N |  |
| 因果连接（因为/所以/因此） |  |  | N |  |
| 第一人称比例（我/我们） |  |  | N |  |
| 第二人称比例（你/你们） |  |  | N |  |
| 确定性语气比例 |  |  | N |  |
| 谨慎语气比例 |  |  | N |  |
| 类比/例子密度（每千字） |  |  | N |  |

### 7.2 结构模板库（Templates）

| template_name | suitable_scenes | skeleton | signature_connectors | example_refs |
|---|---|---|---|---|
| 结论先行-三点论证 |  | 结论→理由1→理由2→理由3→反例→收束句 | 因为/所以/但是 | C-... |

### 7.3 关键词/禁忌词/口癖

| type | items | usage_rule | evidence |
|---|---|---|---|
| keywords |  | 概念口径必须一致 | E-001 |
| taboo_words |  | 违例=0 |  |
| catchphrases |  | 每500字<=2次 |  |

---

## 8) 双重验证记录（Quant + Blind Test）

### 8.1 量化命中表（Generated Text vs Baseline）

| metric | baseline(P25-P75) | generated_value | hit?(Y/N) | deviation_reason | fix |
|---|---|---|---|---|---|
| 平均句长 |  |  |  |  |  |
| 禁忌词违例 | 0 | 0 | Y |  |  |

### 8.2 盲测表（A/B）

| rater | overall(0-5) | structure(0-5) | tone(0-5) | wording(0-5) | rhythm(0-5) | which_more_like?(A/B/Hard) | comments |
|---|---:|---:|---:|---:|---:|---|---|
| 评审1 |  |  |  |  |  |  |  |
