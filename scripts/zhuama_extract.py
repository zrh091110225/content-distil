import argparse
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]


META_RE = {
    "account": re.compile(r"^\s*>\s*公众号[:：]\s*(.+?)\s*$"),
    "published_at": re.compile(r"^\s*>\s*发布时间[:：]\s*(.+?)\s*$"),
    "url": re.compile(r"^\s*>\s*原文链接[:：]\s*(https?://\S+)\s*$"),
}

FRONTMATTER_BLOCK_RE = re.compile(r"^\ufeff?---\s*\n.*?\n---\s*\n?", re.S)
IMG_LINE_RE = re.compile(r"!\[.*?\]\(.*?\)")
WECHAT_REDIRECT_RE = re.compile(r"wechat_redirect", re.I)
IMPORT_FRONTMATTER_RE = re.compile(r"^(title|source|author|published|created|description|tags|mode)\s*:\s*", re.I)
WECHAT_NAV_RE = re.compile(r"(继续滑动看下一个|向上滑动看下一个)")
TITLE_COPY_SUFFIX_RE = re.compile(r"(?:\s+\d+|\((?:副本|\d+)\)|（(?:副本|\d+)）|\s+副本)$", re.I)

TITLE_JUDGMENT_RE = re.compile(r"(本质|真正|关键|不是.+而是|值得|必须|依旧|最迫切|决定|照见|解锁)", re.S)
TITLE_CONFLICT_RE = re.compile(r"(不是.+而是|但|却|别再|不要|劫持|冲突|困境|挣扎|风波|之难|之名)", re.S)
TITLE_COMMAND_RE = re.compile(r"^(别|不要|请|来|去|看|听|读|学)")
TITLE_OBJECT_RE = re.compile(r"(孩子|家长|父母|青少年|年轻人|成员|老师|导演|演员|观众|母亲|父亲|女孩|男孩)")
TITLE_SCENE_RE = re.compile(r"(剧场|舞台|工作坊|招募|抢票|开票|回顾|采访|观后感|活动|课程|旅途|牺牲)")
TITLE_EMOTION_RE = re.compile(r"(恐惧|崩溃|绝望|不甘|挣扎|麻木|焦虑|痛苦|锐利|厚重|劫持)")

OPENING_JUDGMENT_RE = re.compile(r"(本质|真正的问题|最核心|最根本|关键是|这不是.+而是|意味着|其实|说到底)", re.S)
OPENING_MISCONCEPTION_RE = re.compile(r"(很多人以为|你以为|我们以为|常常以为|误以为|但真正|其实不是)", re.S)
OPENING_SCENE_RE = re.compile(r"(在.+?(剧场|课堂|舞台|现场|房间|故事中)|当.+?(时|后)|一次次|那天|此刻|眼前|走进|看见)", re.S)
OPENING_STORY_RE = re.compile(r"(“.+?”|：|一位|一个|有个|有人|她说|他说|孩子们|妈妈|父母|导演|演员)")

CLAIM_STRONG_RE = re.compile(r"(必须|不要|别|应该|值得|本质|关键|真正|最核心|最根本|说到底|不是.+而是)", re.S)
CLAIM_HEDGE_RE = re.compile(r"(可能|也许|或许|大概|一定程度上|相对来说)")

CASE_ROLE_RE = re.compile(r"(孩子|孩子们|家长|父母|母亲|父亲|老师|导演|演员|学员|成员|观众|记者|王后|影子|晨曦|百合|伊菲|阿伽门农|奥德修斯)")
CASE_SCENE_RE = re.compile(r"(剧场|舞台|课堂|房间|现场|军营|学校|家庭|婚礼|风暴|旅程|故事|游戏|探索|排演|创排|采访)")
CASE_DIALOGUE_RE = re.compile(r"(“.+?”|：)")
CASE_ACTION_RE = re.compile(r"(说|问|看见|经历|尝试|走进|进入|站在|坐在|告诉|写下|设计|争吵|崩溃|承受|抢票|开票)")
MARKDOWN_SUBHEADING_RE = re.compile(r"^\s*(#{2,6})\s+(.+?)\s*$")
SECTION_MARKER_RE = re.compile(r"^(0[1-9]|[1-9][0-9]?)[\.、]?\s*$")
SUMMARY_CUE_RE = re.compile(r"(说到底|归根结底|最后|因此|所以|回到|这意味着|真正的问题|最核心|最根本)")
ACTION_CUE_RE = re.compile(r"(你可以|我们可以|让我们|一起|试着|不妨|继续探索|走进剧场|开始)")
CTA_CUE_RE = re.compile(r"(报名|购票|抢票|开票|通道|时间|地点|课程费用|扫码|点击|预约)")

CONNECTOR_TERMS = [
    "但是",
    "但",
    "不过",
    "然而",
    "所以",
    "因此",
    "反过来",
    "说白了",
    "换句话说",
    "更准确地说",
    "你会发现",
]
CONTENT_TERMS = [
    "控制",
    "依恋",
    "成长",
    "主体性",
    "选择",
    "规训",
    "安全感",
    "边界",
    "看见",
    "自我",
    "神谕",
    "人性",
    "关系",
    "故事",
    "探索",
    "真实",
    "冲突",
    "守护",
    "家庭",
    "剧场",
]
JUDGMENT_TERMS = ["本质", "关键", "核心", "真正", "必须", "不要", "不能", "值得", "不值得"]
OBJECT_TERMS = ["孩子", "家长", "父母", "母亲", "父亲", "老师", "导演", "演员", "观众", "青少年", "成人"]
SCENE_TERMS = ["剧场", "舞台", "课堂", "房间", "现场", "家庭", "学校", "工作坊", "故事", "创排", "探索", "旅途", "牺牲"]
FORBIDDEN_TERMS = [
    "赋能",
    "抓手",
    "闭环赋能",
    "底层逻辑",
    "全链路",
    "重塑",
    "生态位",
    "长期主义",
    "高维认知",
    "降维打击",
    "超级个体",
    "个人IP",
    "流量杠杆",
]
STRONG_EMOTION_TERMS = ["恐惧", "崩溃", "绝望", "不甘", "挣扎", "麻木", "焦虑", "痛苦", "愤怒", "孤独", "锐利"]
NEGATION_TERMS = ["不", "没", "无", "别", "不要", "不能", "不是"]
COMFORT_TERMS = ["安全", "很安全", "可以", "没关系", "不必", "一起", "托住", "陪伴", "理解", "看见", "允许"]
ANXIETY_TERMS = ["来不及", "晚了", "危险", "失控", "崩溃", "毁掉", "吞噬", "劫持", "压力", "恐惧", "焦虑"]
AUTHORITY_TERMS = ["必须", "不能", "真正", "关键", "本质", "最核心", "最根本", "说到底", "一定"]
MODEL_CUES = {
    "M1 神谕识别模型": ["神谕", "牺牲", "祭坛", "献祭", "大局", "站队", "舆论", "算法", "规训", "服从", "牺牲"],
    "M2 温柔陷阱模型": ["依恋", "控制", "占有", "吞噬", "边界", "失语", "沉默", "妈妈", "爱", "为你好"],
    "M3 信号翻译与容器模型": ["影子", "容器", "表达", "沉迷", "伪装", "安全", "空间", "托住", "看见", "允许"],
    "M4 象征距离模型": ["故事", "童话", "经典", "想象", "虚构", "角色", "剧场", "寓言", "平行世界", "安全距离"],
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def strip_front_matter(md: str) -> str:
    text = md.lstrip("\ufeff")
    text = FRONTMATTER_BLOCK_RE.sub("", text, count=1)
    return text.strip()


def parse_metadata(md: str) -> dict[str, Any]:
    lines = md.splitlines()
    title = ""
    account = ""
    published_at = ""
    url = ""
    for line in lines[:40]:
        if not title and line.startswith("#"):
            title = line.lstrip("#").strip()
            continue
        if not account:
            m = META_RE["account"].match(line)
            if m:
                account = m.group(1).strip()
                continue
        if not published_at:
            m = META_RE["published_at"].match(line)
            if m:
                published_at = m.group(1).strip()
                continue
        if not url:
            m = META_RE["url"].match(line)
            if m:
                url = m.group(1).strip()
                continue

    return {
        "title": title,
        "account": account,
        "published_at": published_at,
        "url": url,
    }


def normalize_title_for_duplicate_check(title: str) -> str:
    normalized = title.replace("\u3000", " ").strip()
    normalized = re.sub(r"\s+", " ", normalized)
    while True:
        updated = TITLE_COPY_SUFFIX_RE.sub("", normalized).strip()
        if updated == normalized:
            break
        normalized = updated
    return normalized.casefold()


def normalize_date(s: str) -> str:
    s = (s or "").strip()
    if not s:
        return ""
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass
    return s


def clean_body(md: str) -> str:
    lines = []
    for raw in md.splitlines():
        line = raw.strip()
        if not line:
            lines.append("")
            continue
        if IMPORT_FRONTMATTER_RE.match(line):
            continue
        if WECHAT_NAV_RE.search(line):
            continue
        if re.fullmatch(r'抓马教育\s*\*\d{4}年\d{1,2}月\d{1,2}日.*\*', line):
            continue
        if line.startswith(">"):
            continue
        if line.startswith("---"):
            continue
        if IMG_LINE_RE.search(line):
            continue
        if WECHAT_REDIRECT_RE.search(line):
            continue
        if re.fullmatch(r"\*\*演出信\*+息\*\*", line):
            break
        if line.startswith("**|") and ("演出" in line or "票价" in line):
            continue
        lines.append(raw)

    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def split_paragraphs(text: str) -> list[str]:
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    cleaned: list[str] = []
    for p in paras:
        if p.startswith("#"):
            continue
        if p.startswith("**Q") and len(p) <= 12:
            continue
        if re.fullmatch(r"《.+?》\d{4}", p):
            continue
        if p.isdigit():
            continue
        if is_account_date_paragraph(p):
            continue
        cleaned.append(p)
    return cleaned


def extract_subheadings(md: str) -> tuple[list[str], list[int]]:
    headings: list[str] = []
    levels: list[int] = []
    for raw in md.splitlines():
        m = MARKDOWN_SUBHEADING_RE.match(raw.strip())
        if not m:
            continue
        level = len(m.group(1))
        if level < 2:
            continue
        headings.append(m.group(2).strip())
        levels.append(level)
    return headings, levels


def topic_from_filename(name: str) -> str:
    n = name
    if "《旅途》" in n or "旅途" in n:
        return "旅途"
    if "《牺牲》" in n or "牺牲" in n:
        return "牺牲"
    if "工作坊" in n or "大师工作坊" in n:
        return "工作坊"
    if "招募" in n or "成员招募" in n:
        return "招募"
    if "回顾" in n or "研究室" in n:
        return "研究室/回顾"
    if "开票" in n or "开年" in n or "抢票" in n or "开票丨" in n:
        return "开票/票务"
    if "观后感" in n:
        return "观后感"
    return "其他"


def tokenize_zh(text: str) -> list[str]:
    t = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]+", " ", text)
    parts = [p.strip() for p in t.split() if p.strip()]
    tokens: list[str] = []
    for p in parts:
        if re.fullmatch(r"[A-Za-z0-9]{1,2}", p):
            continue
        if len(p) == 1:
            continue
        tokens.append(p)
    return tokens


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"[。！？!?]\s*", text) if s.strip()]


def percentile(arr: list[int], p: float) -> int:
    if not arr:
        return 0
    idx = int(round((len(arr) - 1) * p))
    return arr[max(0, min(len(arr) - 1, idx))]


def stats_from_numbers(nums: list[int | float]) -> dict[str, Any]:
    if not nums:
        return {}
    arr = sorted(nums)
    return {
        "mean": sum(arr) / len(arr),
        "p25": percentile([int(x) for x in arr], 0.25),
        "p50": percentile([int(x) for x in arr], 0.50),
        "p75": percentile([int(x) for x in arr], 0.75),
        "count": len(arr),
    }


def detect_title_sentence_type(title: str) -> str:
    if "?" in title or "？" in title:
        return "question"
    if "!" in title or "！" in title:
        return "exclamation"
    if TITLE_COMMAND_RE.search(title):
        return "command"
    if TITLE_JUDGMENT_RE.search(title):
        return "judgment"
    return "statement"


def first_signal_char_position(text: str, pattern: re.Pattern[str], limit: int = 300) -> int | None:
    head = text[:limit]
    m = pattern.search(head)
    if not m:
        return None
    return m.start() + 1


def is_case_paragraph(paragraph: str) -> bool:
    if len(paragraph) < 30:
        return False
    score = 0
    if CASE_DIALOGUE_RE.search(paragraph):
        score += 1
    if CASE_ROLE_RE.search(paragraph):
        score += 1
    if CASE_SCENE_RE.search(paragraph):
        score += 1
    if CASE_ACTION_RE.search(paragraph):
        score += 1
    return score >= 2


CLAIM_SIGNAL_RE = re.compile(
    r"(必须|不要|别|需要|应该|值得|最.*?是|其实|真正|不是|而是|警惕|关键|本质|最大的|太.*?了|你要|我们要|要学会|别以为|往深|取决于|如果|那么|因为|所以|因此)"
)


def extract_claim_candidates(paras: Iterable[str]) -> list[dict[str, Any]]:
    cands: list[dict[str, Any]] = []
    for i, p in enumerate(paras, start=1):
        if len(p) < 18:
            continue
        if "?" in p or "？" in p or CLAIM_SIGNAL_RE.search(p):
            cands.append(
                {
                    "para_index": i,
                    "text": p,
                    "signals": sorted(set(CLAIM_SIGNAL_RE.findall(p))),
                }
            )
    return cands


@dataclass
class ContentItem:
    content_id: str
    path: Path
    title: str
    account: str
    published_at: str
    url: str
    topic: str
    body: str
    paragraphs: list[str]
    subheadings: list[str]
    heading_levels: list[int]
    file_hash: str
    status: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="提取内容索引、统计基线与增量维护状态。")
    parser.add_argument("--corpus", default="zhuama", help="语料目录名，默认 zhuama")
    parser.add_argument("--docs-dir", type=Path, help="语料目录，默认 docs/<corpus>")
    parser.add_argument("--out-dir", type=Path, help="输出目录，默认 outputs/<corpus>")
    parser.add_argument("--holdout-ratio", type=float, default=0.2, help="验证集比例，默认 0.2")
    return parser.parse_args()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def manifest_by_file(manifest: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not manifest:
        return {}
    items = manifest.get("items", [])
    return {it["file"]: it for it in items}


def next_content_id(existing_manifest: dict[str, Any] | None) -> int:
    max_id = 0
    if not existing_manifest:
        return 1
    for it in existing_manifest.get("items", []):
        cid = str(it.get("content_id", ""))
        if cid.startswith("C-") and cid[2:].isdigit():
            max_id = max(max_id, int(cid[2:]))
    return max_id + 1


def build_items(
    docs_dir: Path,
    root: Path,
    previous_manifest: dict[str, Any] | None,
) -> list[ContentItem]:
    items: list[ContentItem] = []
    prev_by_file = manifest_by_file(previous_manifest)
    next_id = next_content_id(previous_manifest)
    for p in sorted(docs_dir.glob("*.md")):
        original_raw = read_text(p)
        raw = strip_front_matter(original_raw)
        meta = parse_metadata(raw)
        body = clean_body(raw)
        paras = split_paragraphs(body)
        subheadings, heading_levels = extract_subheadings(raw)
        rel = str(p.relative_to(root))
        file_hash = sha256_text(original_raw)
        prev = prev_by_file.get(rel)
        if prev:
            content_id = prev["content_id"]
            status = "unchanged" if prev.get("file_hash") == file_hash else "updated"
        else:
            content_id = f"C-{next_id:04d}"
            next_id += 1
            status = "new"
        items.append(
            ContentItem(
                content_id=content_id,
                path=p,
                title=meta["title"] or p.stem,
                account=meta["account"] or "抓马教育",
                published_at=normalize_date(meta["published_at"]),
                url=meta["url"],
                topic=topic_from_filename(p.stem),
                body=body,
                paragraphs=paras,
                subheadings=subheadings,
                heading_levels=heading_levels,
                file_hash=file_hash,
                status=status,
            )
        )
    return items


def find_changed_title_duplicates(items: list[ContentItem]) -> list[list[ContentItem]]:
    by_title: dict[str, list[ContentItem]] = defaultdict(list)
    for it in items:
        key = normalize_title_for_duplicate_check(it.title or it.path.stem)
        by_title[key].append(it)

    duplicate_groups: list[list[ContentItem]] = []
    for key, group in by_title.items():
        if not key or len(group) < 2:
            continue
        if any(it.status in {"new", "updated"} for it in group):
            duplicate_groups.append(sorted(group, key=lambda it: (it.status != "new", str(it.path))))
    return duplicate_groups


def raise_on_changed_title_duplicates(items: list[ContentItem], root: Path) -> None:
    duplicate_groups = find_changed_title_duplicates(items)
    if not duplicate_groups:
        return

    lines = ["检测到新增或更新文章的标题重复，请先处理后再运行增量提取：", ""]
    for group in duplicate_groups:
        canonical_title = normalize_title_for_duplicate_check(group[0].title or group[0].path.stem)
        lines.append(f"- 归一化标题：{canonical_title}")
        for it in group:
            rel = it.path.relative_to(root)
            lines.append(f"  - [{it.status}] {it.title} ({rel})")
        lines.append("")
    raise SystemExit("\n".join(lines).rstrip())


def stratified_holdout(items: list[ContentItem], ratio: float = 0.2) -> tuple[list[ContentItem], list[ContentItem]]:
    by_topic: dict[str, list[ContentItem]] = defaultdict(list)
    for it in items:
        by_topic[it.topic].append(it)

    holdout: list[ContentItem] = []
    train: list[ContentItem] = []
    for topic, arr in sorted(by_topic.items(), key=lambda x: x[0]):
        arr_sorted = sorted(arr, key=lambda x: x.published_at or x.path.stem)
        k = max(1, int(math.ceil(len(arr_sorted) * ratio))) if len(arr_sorted) >= 5 else max(1, int(round(len(arr_sorted) * ratio)))
        picks = arr_sorted[-k:]
        holdout.extend(picks)
        holdout_set = {p.path for p in picks}
        train.extend([x for x in arr_sorted if x.path not in holdout_set])

    holdout_set2 = {x.path for x in holdout}
    train = [x for x in items if x.path not in holdout_set2]
    return train, holdout


def compute_style_metrics(items: list[ContentItem]) -> dict[str, Any]:
    sentences: list[str] = []
    total_chars = 0
    question_count = 0
    imperative_count = 0
    turn_count = 0
    causal_count = 0
    first_person = 0
    second_person = 0
    certain_count = 0
    hedged_count = 0
    analogy_count = 0

    for it in items:
        text = "\n".join(it.paragraphs)
        total_chars += len(text)
        sents = split_sentences(text)
        sentences.extend(sents)

        question_count += text.count("？") + text.count("?")
        imperative_count += len(re.findall(r"(你要|不要|别|请|务必|必须)", text))
        turn_count += len(re.findall(r"(但是|然而|不过|但)", text))
        causal_count += len(re.findall(r"(因为|所以|因此)", text))
        first_person += len(re.findall(r"(我|我们)", text))
        second_person += len(re.findall(r"(你|你们)", text))
        certain_count += len(re.findall(r"(一定|显然|必须|肯定)", text))
        hedged_count += len(re.findall(r"(可能|也许|大概|或许)", text))
        analogy_count += len(re.findall(r"(像|如同|仿佛|就像|好比)", text))

    sent_lens = [len(s) for s in sentences if s]
    sent_lens_sorted = sorted(sent_lens)
    if not sent_lens_sorted:
        return {}

    return {
        "sentence_length": {
            "mean": sum(sent_lens_sorted) / len(sent_lens_sorted),
            "p25": percentile(sent_lens_sorted, 0.25),
            "p50": percentile(sent_lens_sorted, 0.50),
            "p75": percentile(sent_lens_sorted, 0.75),
            "count": len(sent_lens_sorted),
        },
        "question_marks": question_count,
        "imperative_signals": imperative_count,
        "turn_signals": turn_count,
        "causal_signals": causal_count,
        "first_person_tokens": first_person,
        "second_person_tokens": second_person,
        "certainty_tokens": certain_count,
        "hedge_tokens": hedged_count,
        "analogy_tokens": analogy_count,
        "total_chars": total_chars,
    }


def compute_title_metrics(items: list[ContentItem]) -> dict[str, Any]:
    lengths: list[int] = []
    sentence_types = Counter()
    front_conclusion = 0
    conflict = 0
    digits = 0
    object_titles = 0
    scene_titles = 0
    emotion_titles = 0

    for it in items:
        title = (it.title or "").strip()
        if not title:
            continue
        lengths.append(len(title))
        sentence_types[detect_title_sentence_type(title)] += 1
        if TITLE_JUDGMENT_RE.search(title):
            front_conclusion += 1
        if TITLE_CONFLICT_RE.search(title):
            conflict += 1
        if re.search(r"\d", title):
            digits += 1
        if TITLE_OBJECT_RE.search(title):
            object_titles += 1
        if TITLE_SCENE_RE.search(title):
            scene_titles += 1
        if TITLE_EMOTION_RE.search(title):
            emotion_titles += 1

    total = len(items) or 1
    return {
        "length": stats_from_numbers(lengths),
        "sentence_types": dict(sentence_types),
        "front_conclusion_rate": round(front_conclusion / total, 4),
        "conflict_rate": round(conflict / total, 4),
        "digit_rate": round(digits / total, 4),
        "object_word_rate": round(object_titles / total, 4),
        "scene_word_rate": round(scene_titles / total, 4),
        "emotion_word_rate": round(emotion_titles / total, 4),
    }


def compute_opening_metrics(items: list[ContentItem]) -> dict[str, Any]:
    core_positions: list[int] = []
    question_counts: list[int] = []
    has_conclusion = 0
    misconception_open = 0
    scene_open = 0
    story_open = 0

    for it in items:
        text = "\n".join(it.paragraphs).strip()
        opening = text[:300]
        if not opening:
            continue
        pos = first_signal_char_position(text, OPENING_JUDGMENT_RE, limit=300)
        if pos is not None:
            core_positions.append(pos)
            has_conclusion += 1
        if OPENING_MISCONCEPTION_RE.search(opening):
            misconception_open += 1
        if OPENING_SCENE_RE.search(opening):
            scene_open += 1
        if OPENING_STORY_RE.search(opening):
            story_open += 1
        question_counts.append(opening.count("？") + opening.count("?"))

    total = len(items) or 1
    return {
        "core_judgment_char_position": stats_from_numbers(core_positions),
        "question_count_in_first_300_chars": stats_from_numbers(question_counts),
        "has_conclusion_rate": round(has_conclusion / total, 4),
        "misconception_open_rate": round(misconception_open / total, 4),
        "scene_open_rate": round(scene_open / total, 4),
        "story_open_rate": round(story_open / total, 4),
    }


def compute_viewpoint_metrics(items: list[ContentItem]) -> dict[str, Any]:
    total_chars = 0
    claim_count = 0
    strong_count = 0
    hedge_count = 0

    for it in items:
        text = "\n".join(it.paragraphs)
        total_chars += len(text)
        claim_count += len(extract_claim_candidates(it.paragraphs))
        strong_count += len(CLAIM_STRONG_RE.findall(text))
        hedge_count += len(CLAIM_HEDGE_RE.findall(text))

    per_500 = round(claim_count / total_chars * 500, 4) if total_chars else 0
    total_judgment_tokens = strong_count + hedge_count
    return {
        "claim_count_per_500_chars": per_500,
        "strong_judgment_count": strong_count,
        "hedge_count": hedge_count,
        "strong_judgment_ratio": round(strong_count / total_judgment_tokens, 4) if total_judgment_tokens else 0,
        "hedge_ratio": round(hedge_count / total_judgment_tokens, 4) if total_judgment_tokens else 0,
        "redefinition_count": None,
        "redefinition_note": "该指标按用户要求保留给 LLM/人工判断，不做程序硬统计。",
    }


def compute_case_metrics(items: list[ContentItem]) -> dict[str, Any]:
    case_para_count = 0
    case_para_lengths: list[int] = []
    role_counter: Counter[str] = Counter()
    scene_counter: Counter[str] = Counter()
    total_chars = 0
    analogy_count = 0

    role_keywords = ["孩子", "家长", "父母", "母亲", "父亲", "老师", "导演", "演员", "学员", "成员", "观众", "记者"]
    scene_keywords = ["剧场", "舞台", "课堂", "房间", "现场", "学校", "家庭", "婚礼", "军营", "采访", "游戏", "探索", "排演", "创排"]

    for it in items:
        text = "\n".join(it.paragraphs)
        total_chars += len(text)
        analogy_count += len(re.findall(r"(像|如同|仿佛|就像|好比)", text))
        for p in it.paragraphs:
            if not is_case_paragraph(p):
                continue
            case_para_count += 1
            case_para_lengths.append(len(p))
            for kw in role_keywords:
                if kw in p:
                    role_counter[kw] += 1
            for kw in scene_keywords:
                if kw in p:
                    scene_counter[kw] += 1

    return {
        "case_paragraphs_per_1000_chars": round(case_para_count / total_chars * 1000, 4) if total_chars else 0,
        "case_paragraph_count": case_para_count,
        "case_paragraph_length": stats_from_numbers(case_para_lengths),
        "top_roles": role_counter.most_common(10),
        "top_scenes": scene_counter.most_common(10),
        "analogy_per_1000_chars": round(analogy_count / total_chars * 1000, 4) if total_chars else 0,
    }


def compute_structure_metrics(
    items: list[ContentItem],
    style_metrics: dict[str, Any],
    viewpoint_metrics: dict[str, Any],
) -> dict[str, Any]:
    subheading_counts = [len(it.subheadings) for it in items]
    subheading_lengths = [len(h) for it in items for h in it.subheadings]
    explicit_articles = sum(1 for it in items if it.subheadings)
    max_depths = [(max(it.heading_levels) - 1) for it in items if it.heading_levels]
    total_case = 0
    bucket_counts = {"front": 0, "middle": 0, "tail": 0}
    summary_tail = 0
    action_tail = 0
    cta_tail = 0
    numbered_marker_articles = 0

    for it in items:
        paras = it.paragraphs
        if any(SECTION_MARKER_RE.match(p.strip()) for p in paras):
            numbered_marker_articles += 1
        n = len(paras)
        for idx, p in enumerate(paras):
            if not is_case_paragraph(p):
                continue
            total_case += 1
            ratio = idx / max(1, n)
            if ratio < 1 / 3:
                bucket_counts["front"] += 1
            elif ratio < 2 / 3:
                bucket_counts["middle"] += 1
            else:
                bucket_counts["tail"] += 1
        tail_paras = paras[-2:] if len(paras) >= 2 else paras
        tail_text = "\n".join(tail_paras)
        if SUMMARY_CUE_RE.search(tail_text):
            summary_tail += 1
        if ACTION_CUE_RE.search(tail_text):
            action_tail += 1
        if CTA_CUE_RE.search(tail_text):
            cta_tail += 1

    total_chars = style_metrics.get("total_chars", 0) or 1
    return {
        "subheading_count": stats_from_numbers(subheading_counts),
        "subheading_article_rate": round(explicit_articles / (len(items) or 1), 4),
        "subheading_length": stats_from_numbers(subheading_lengths),
        "claim_count_per_500_chars": viewpoint_metrics["claim_count_per_500_chars"],
        "turn_signals_per_1000_chars": round(style_metrics["turn_signals"] / total_chars * 1000, 4),
        "case_bucket_distribution": {
            key: round(value / total_case, 4) if total_case else 0 for key, value in bucket_counts.items()
        },
        "numbered_section_article_rate": round(numbered_marker_articles / (len(items) or 1), 4),
        "depth": stats_from_numbers(max_depths),
        "tail_summary_rate": round(summary_tail / (len(items) or 1), 4),
        "tail_action_rate": round(action_tail / (len(items) or 1), 4),
        "tail_cta_rate": round(cta_tail / (len(items) or 1), 4),
    }


def count_terms(text: str, terms: list[str]) -> list[tuple[str, int]]:
    counts: list[tuple[str, int]] = []
    for term in terms:
        n = text.count(term)
        if n:
            counts.append((term, n))
    counts.sort(key=lambda x: (-x[1], x[0]))
    return counts


def compute_vocab_metrics(items: list[ContentItem]) -> dict[str, Any]:
    text = "\n".join("\n".join(it.paragraphs) for it in items)
    total_chars = len(text) or 1
    content_words = count_terms(text, CONTENT_TERMS)
    connectors = count_terms(text, CONNECTOR_TERMS)
    judgments = count_terms(text, JUDGMENT_TERMS)
    objects = count_terms(text, OBJECT_TERMS)
    scenes = count_terms(text, SCENE_TERMS)
    forbidden = count_terms(text, FORBIDDEN_TERMS)
    return {
        "top_content_words": content_words[:10],
        "top_connectors": connectors[:8],
        "top_judgment_words": judgments[:8],
        "top_object_words": objects[:8],
        "top_scene_words": scenes[:8],
        "forbidden_words": forbidden,
        "forbidden_hit_count": sum(count for _, count in forbidden),
        "forbidden_hit_per_1000_chars": round(sum(count for _, count in forbidden) / total_chars * 1000, 4),
    }


def compute_emotion_metrics(items: list[ContentItem]) -> dict[str, Any]:
    text = "\n".join("\n".join(it.paragraphs) for it in items)
    total_chars = len(text) or 1
    strong_emotion = count_terms(text, STRONG_EMOTION_TERMS)
    comfort = count_terms(text, COMFORT_TERMS)
    anxiety = count_terms(text, ANXIETY_TERMS)
    authority = count_terms(text, AUTHORITY_TERMS)
    negation_count = sum(len(re.findall(term, text)) for term in NEGATION_TERMS)
    return {
        "strong_emotion_words": strong_emotion[:10],
        "strong_emotion_per_1000_chars": round(sum(count for _, count in strong_emotion) / total_chars * 1000, 4),
        "negation_per_1000_chars": round(negation_count / total_chars * 1000, 4),
        "comfort_words": comfort[:10],
        "comfort_per_1000_chars": round(sum(count for _, count in comfort) / total_chars * 1000, 4),
        "authority_words": authority[:10],
        "authority_per_1000_chars": round(sum(count for _, count in authority) / total_chars * 1000, 4),
        "anxiety_words": anxiety[:10],
        "anxiety_per_1000_chars": round(sum(count for _, count in anxiety) / total_chars * 1000, 4),
    }


def top_keywords(items: list[ContentItem], top_k: int = 80) -> list[tuple[str, int]]:
    stop = {
        "一个",
        "我们",
        "你们",
        "他们",
        "因为",
        "所以",
        "但是",
        "不过",
        "这个",
        "那个",
        "什么",
        "不是",
        "而是",
        "如果",
        "这样",
        "可以",
        "自己",
        "孩子",
        "家长",
        "少年",
        "剧场",
        "剧团",
        "演出",
        "作品",
    }
    c = Counter()
    for it in items:
        tokens = tokenize_zh("\n".join(it.paragraphs))
        for t in tokens:
            if t in stop:
                continue
            if len(t) > 20:
                continue
            c[t] += 1
    return c.most_common(top_k)


def ensure_dirs(out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    state_dir = out_dir / "state"
    generated_dir = out_dir / "generated"
    state_dir.mkdir(parents=True, exist_ok=True)
    generated_dir.mkdir(parents=True, exist_ok=True)
    return state_dir, generated_dir


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def summarize_item(it: ContentItem, root: Path) -> dict[str, Any]:
    return {
        "content_id": it.content_id,
        "file": str(it.path.relative_to(root)),
        "title": it.title,
        "account": it.account,
        "published_at": it.published_at,
        "url": it.url,
        "topic": it.topic,
        "paragraph_count": len(it.paragraphs),
        "file_hash": it.file_hash,
        "status": it.status,
    }


def get_nested(data: dict[str, Any] | None, path: str) -> float | int | None:
    if not data:
        return None
    cur: Any = data
    for key in path.split("."):
        if not isinstance(cur, dict) or key not in cur:
            return None
        cur = cur[key]
    if isinstance(cur, (int, float)):
        return cur
    return None


def compare_numeric_metric(
    previous: dict[str, Any] | None,
    current: dict[str, Any],
    path: str,
    label: str,
    threshold: float,
) -> str | None:
    old_val = get_nested(previous, path)
    new_val = get_nested(current, path)
    if old_val is None or new_val is None:
        return None
    if abs(float(new_val) - float(old_val)) < threshold:
        return None
    if isinstance(old_val, int) and isinstance(new_val, int):
        return f"- {label}：{old_val} -> {new_val}"
    return f"- {label}：{old_val:.4f} -> {new_val:.4f}"


def clip_text(text: str, limit: int = 120) -> str:
    one_line = re.sub(r"\s+", " ", text).strip()
    return one_line if len(one_line) <= limit else one_line[: limit - 1] + "…"


def strip_markdown_noise(text: str) -> str:
    cleaned = re.sub(r"^\s*[-*+]\s*", "", text.strip())
    cleaned = re.sub(r"\[\[(.+?)\]\]", r"\1", cleaned)
    cleaned = re.sub(r"[*_`#>]+", "", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip(" -")


def normalize_candidate_excerpt(text: str, limit: int = 140) -> str:
    lines: list[str] = []
    for raw in text.splitlines():
        line = strip_markdown_noise(raw)
        if not line:
            continue
        if line.startswith("<video") or line.startswith("<img"):
            continue
        if line.startswith("[["):
            continue
        if re.fullmatch(r"\*?\d{4}年?\d{0,2}.*", line):
            continue
        if line in {"抓马教育 - 公众号", "抓马教育 - 文章", "抓马教育 公众号", "抓马教育 文章"}:
            continue
        if is_account_date_paragraph(line):
            continue
        if is_candidate_noise_paragraph(line):
            continue
        lines.append(line)
    return clip_text(" ".join(lines), limit=limit)


def count_term_hits(text: str, terms: list[str]) -> int:
    return sum(text.count(term) for term in terms)


def paragraph_signal_score(paragraph: str, terms: list[str]) -> int:
    return count_term_hits(paragraph, terms)


def item_signal_score(item: ContentItem, terms: list[str]) -> int:
    text = "\n".join(item.paragraphs)
    return count_term_hits(text, terms)


def is_account_date_paragraph(paragraph: str) -> bool:
    return bool(
        re.fullmatch(r"(抓马教育|Chris Cooper)\s+\*?\d{4}年\d{1,2}月\d{1,2}日.*\*?", paragraph.strip())
    )


def is_bio_paragraph(paragraph: str) -> bool:
    bio_terms = [
        "毕业于",
        "培训师",
        "导师",
        "创意总监",
        "艺术总监",
        "著名演员",
        "剧作家",
        "导演",
        "代表作",
        "曾参加",
        "认证",
        "学院",
        "工作经历",
        "课程创作",
    ]
    return sum(1 for term in bio_terms if term in paragraph) >= 2


def is_candidate_noise_paragraph(paragraph: str) -> bool:
    text = strip_markdown_noise(paragraph)
    if not text:
        return True
    if text.startswith("<video") or text.startswith("<img"):
        return True
    short_labels = {
        "编剧自述",
        "直面鸿沟青年剧团往期作品",
        "《牺牲》排练剧照",
        "《牺牲》故事探索",
        "工作坊时间",
        "工作坊地点",
        "工作坊咨询",
        "工作坊引导者",
        "深度戏剧工作坊",
    }
    if text in short_labels:
        return True
    if len(text) <= 24 and re.fullmatch(r"(文/)?[A-Za-z\u4e00-\u9fff·\s]+", text):
        return True
    if re.fullmatch(r"\d{4}年《.+》", text):
        return True
    if text.count("|") >= 3:
        return True
    if re.fullmatch(r"[▶•·]?\s*(编剧|导演|监制|出品|演员|舞台监督|舞美设计|音效设计|平面设计|剧照)\s*[：:|]?", text):
        return True

    noise_groups = [
        ["招募", "工作坊"],
        ["报名", "课程"],
        ["购票", "开票"],
        ["时间", "地点"],
        ["演出", "咨询"],
        ["剧团", "作品"],
        ["剧团", "创排"],
        ["创意总监", "戏剧构作"],
        ["艺术总监", "剧作家"],
        ["教育戏剧", "培训"],
        ["成员", "招募"],
    ]
    if any(all(term in text for term in group) for group in noise_groups):
        return True

    noisy_markers = [
        "抓马.少年剧场",
        "直面鸿沟青年剧团",
        "工作坊",
        "报名通道",
        "课程费用",
        "演出时间",
        "演出地点",
        "购票",
        "开票",
        "票务",
        "抢票",
        "创意总监",
        "艺术总监",
        "著名演员",
        "剧作家和导演",
        "代表作",
        "国际知名",
        "教育戏剧导师",
        "认证培训师",
    ]
    if sum(1 for marker in noisy_markers if marker in text) >= 2:
        return True

    return False


def select_representative_excerpt(
    item: ContentItem,
    preferred_terms: list[str] | None = None,
    fallback_limit: int = 220,
    max_paragraphs: int | None = None,
) -> str:
    preferred_terms = preferred_terms or []
    scored: list[tuple[int, str]] = []
    paragraphs = item.paragraphs[:max_paragraphs] if max_paragraphs else item.paragraphs
    for para in paragraphs:
        if is_account_date_paragraph(para) or is_candidate_noise_paragraph(para) or is_bio_paragraph(para):
            continue
        score = len(para)
        if preferred_terms:
            score += count_term_hits(para, preferred_terms) * 10
        if is_case_paragraph(para):
            score += 8
        if CLAIM_SIGNAL_RE.search(para):
            score += 5
        scored.append((score, para))
    if scored:
        scored.sort(key=lambda x: x[0], reverse=True)
        return normalize_candidate_excerpt(scored[0][1], limit=140)
    return normalize_candidate_excerpt(item.body[:fallback_limit], limit=140)


def build_review_queue(
    corpus: str,
    root: Path,
    out_dir: Path,
    items: list[ContentItem],
    train: list[ContentItem],
    holdout: list[ContentItem],
    previous_manifest: dict[str, Any] | None,
    previous_summary: dict[str, Any] | None,
    current_summary: dict[str, Any],
) -> str:
    new_items = [it for it in items if it.status == "new"]
    updated_items = [it for it in items if it.status == "updated"]
    unchanged_count = len([it for it in items if it.status == "unchanged"])

    prev_topics = (previous_summary or {}).get("topics", {})
    cur_topics = current_summary.get("topics", {})
    topic_lines: list[str] = []
    for topic in sorted(set(prev_topics) | set(cur_topics)):
        old = int(prev_topics.get(topic, 0))
        new = int(cur_topics.get(topic, 0))
        if old != new:
            topic_lines.append(f"- {topic}：{old} -> {new}")

    metric_lines = [
        compare_numeric_metric(previous_summary, current_summary, "style_metrics.sentence_length.p50", "句长 P50", 2),
        compare_numeric_metric(previous_summary, current_summary, "title_metrics.length.p50", "标题长度 P50", 1),
        compare_numeric_metric(previous_summary, current_summary, "opening_metrics.scene_open_rate", "开头场景切入率", 0.05),
        compare_numeric_metric(previous_summary, current_summary, "viewpoint_metrics.claim_count_per_500_chars", "每 500 字观点密度", 0.08),
        compare_numeric_metric(previous_summary, current_summary, "case_metrics.case_paragraphs_per_1000_chars", "每千字案例段落数", 0.2),
    ]
    metric_lines = [line for line in metric_lines if line]

    prev_holdout_files = {
        it["file"]
        for it in (previous_manifest or {}).get("items", [])
        if it.get("split") == "holdout"
    }
    cur_holdout_files = {str(it.path.relative_to(root)) for it in holdout}
    holdout_changed = prev_holdout_files != cur_holdout_files if previous_manifest else bool(new_items or updated_items)

    review_docs: list[str] = []
    if topic_lines:
        review_docs.append(f"- `taxonomy.md`：主题分布发生变化，需确认是否出现新主题或旧主题权重漂移。")
    if new_items or updated_items or metric_lines:
        review_docs.append(f"- `style_dna.md`：A 类统计和典型样本候选需要复核。")
        review_docs.append(f"- `style_spec.md`：若标题/开头/案例/观点指标出现漂移，需同步检查执行约束。")
    if new_items or updated_items:
        review_docs.append(f"- `beliefs_models.md`：新文章可能补充模型证据、边界或反例。")
    if holdout_changed:
        review_docs.append(f"- `validation_report.md`：holdout 清单变化，建议补一轮复测。")

    if not review_docs:
        review_docs.append("- 当前没有必须人工更新的长期文档，可仅保留本轮自动统计结果。")

    lines = [
        f"# {corpus} 增量复核队列",
        "",
        f"- 生成时间：{current_summary['generated_at']}",
        f"- 总文章数：{len(items)}",
        f"- 训练集：{len(train)}",
        f"- 验证集：{len(holdout)}",
        f"- 新增：{len(new_items)} 篇",
        f"- 更新：{len(updated_items)} 篇",
        f"- 未变化：{unchanged_count} 篇",
        "",
        "## 本轮新增/更新文章",
        "",
    ]
    if not new_items and not updated_items:
        lines.append("- 无新增或变更文章。")
    else:
        for it in new_items + updated_items:
            lines.append(
                f"- `{it.status}` {it.content_id} [{it.title}](file://{it.path})"
                f" ({it.topic}, {str(it.path.relative_to(root))})"
            )

    lines.extend(["", "## 主题变化", ""])
    if topic_lines:
        lines.extend(topic_lines)
    else:
        lines.append("- 主题分布无显著变化。")

    lines.extend(["", "## 关键指标变化", ""])
    if metric_lines:
        lines.extend(metric_lines)
    else:
        lines.append("- 关键 A 类指标无显著变化。")

    lines.extend(["", "## 建议复核文档", ""])
    lines.extend(review_docs)

    lines.extend(
        [
            "",
            "## 建议动作",
            "",
            "- 先查看 `state/manifest.json` 中本轮 `new/updated` 文章，确认元数据与主题归类是否正确。",
            f"- 复核 `generated/typical_sample_candidates.md`：从 8 层候选里挑选可补进 `style_dna.md` 的典型样本。",
            f"- 复核 `generated/model_retest_candidates.md`：从 holdout 候选里挑 2-3 篇补做模型复测或边界校正。",
            "- 若只新增少量文章，可先更新 `style_dna.md` 的 A 类统计和典型样本候选，不急于改动 B/C/D。",
            "- 若主题分布或 holdout 发生变化，优先补 `validation_report.md` 的复测记录。",
            "- 当新增文章累计超过现有语料的 10%-20% 时，建议做一次完整月度重更新。",
        ]
    )
    return "\n".join(lines) + "\n"


def append_changelog(
    changelog_path: Path,
    items: list[ContentItem],
    current_summary: dict[str, Any],
) -> None:
    new_items = [it for it in items if it.status == "new"]
    updated_items = [it for it in items if it.status == "updated"]
    lines = [
        f"## {current_summary['generated_at']}",
        "",
        f"- 总文章数：{current_summary['total']}",
        f"- 训练集 / 验证集：{current_summary['train']} / {current_summary['holdout']}",
        f"- 本轮新增：{len(new_items)} 篇",
        f"- 本轮更新：{len(updated_items)} 篇",
    ]
    if new_items:
        lines.append("- 新增条目：")
        lines.extend([f"  - {it.content_id} {it.title}" for it in new_items])
    if updated_items:
        lines.append("- 更新条目：")
        lines.extend([f"  - {it.content_id} {it.title}" for it in updated_items])
    lines.append("")
    existing = changelog_path.read_text(encoding="utf-8") if changelog_path.exists() else "# 增量变更日志\n\n"
    changelog_path.write_text(existing + "\n".join(lines) + "\n", encoding="utf-8")


def build_typical_sample_candidates(root: Path, items: list[ContentItem]) -> str:
    title_ranked = sorted(
        items,
        key=lambda it: (
            int(bool(TITLE_SCENE_RE.search(it.title))),
            int(bool(TITLE_CONFLICT_RE.search(it.title))),
            int(bool(TITLE_JUDGMENT_RE.search(it.title))),
            len(it.title),
        ),
        reverse=True,
    )[:5]

    opening_ranked = sorted(
        items,
        key=lambda it: (
            int(bool(OPENING_SCENE_RE.search(it.body[:300]))),
            int(bool(OPENING_STORY_RE.search(it.body[:300]))),
            int(bool(OPENING_JUDGMENT_RE.search(it.body[:300]))),
            it.body[:300].count("？") + it.body[:300].count("?"),
        ),
        reverse=True,
    )[:5]

    structure_ranked = sorted(
        items,
        key=lambda it: (
            len(it.subheadings),
            int(any(SECTION_MARKER_RE.match(p.strip()) for p in it.paragraphs)),
            len(extract_claim_candidates(it.paragraphs)),
        ),
        reverse=True,
    )[:5]

    syntax_candidates: list[tuple[int, ContentItem, str]] = []
    viewpoint_candidates: list[tuple[int, ContentItem, str]] = []
    case_candidates: list[tuple[int, ContentItem, str]] = []
    emotion_candidates: list[tuple[int, ContentItem, str]] = []
    for it in items:
        for p in it.paragraphs:
            syntax_score = (
                int("？" in p or "?" in p)
                + count_term_hits(p, ["不是", "而是", "真正", "本质", "关键", "说白了"])
                + count_term_hits(p, ["但是", "然而", "不过", "但"])
            )
            if syntax_score >= 2:
                syntax_candidates.append((syntax_score, it, p))

            viewpoint_score = (
                count_term_hits(p, ["不是", "而是", "真正的问题", "最核心", "最根本", "本质"])
                + count_term_hits(p, ["控制", "主体性", "规训", "选择", "边界"])
            )
            if viewpoint_score >= 2:
                viewpoint_candidates.append((viewpoint_score, it, p))

            case_score = 0
            if (
                is_case_paragraph(p)
                and not is_bio_paragraph(p)
                and not is_candidate_noise_paragraph(p)
                and not is_account_date_paragraph(p)
            ):
                case_score = (
                    count_term_hits(p, ["孩子", "母亲", "父母", "导演", "演员", "观众", "老师"])
                    + count_term_hits(p, ["剧场", "舞台", "家庭", "学校", "房间", "课堂", "现场"])
                    + count_term_hits(p, ["说", "问", "看见", "站在", "走进", "争吵", "崩溃", "承受"])
                )
            if case_score >= 3:
                case_candidates.append((case_score, it, p))

            emotion_score = (
                paragraph_signal_score(p, STRONG_EMOTION_TERMS)
                + paragraph_signal_score(p, COMFORT_TERMS)
                + paragraph_signal_score(p, AUTHORITY_TERMS)
            )
            if emotion_score >= 2:
                emotion_candidates.append((emotion_score, it, p))

    syntax_ranked = sorted(syntax_candidates, key=lambda x: (x[0], len(x[2])), reverse=True)[:5]
    viewpoint_ranked = sorted(viewpoint_candidates, key=lambda x: (x[0], len(x[2])), reverse=True)[:5]
    case_ranked = sorted(case_candidates, key=lambda x: (x[0], len(x[2])), reverse=True)[:5]
    emotion_ranked = sorted(emotion_candidates, key=lambda x: (x[0], len(x[2])), reverse=True)[:5]

    vocab_ranked = sorted(
        items,
        key=lambda it: item_signal_score(it, CONTENT_TERMS) + item_signal_score(it, JUDGMENT_TERMS),
        reverse=True,
    )[:5]

    lines = [
        "# 典型样本候选",
        "",
        "用途：为 `style_dna.md` 的“典型样本”人工复核提供候选，不直接自动写入主文档。",
        "",
        "说明：",
        "- 候选来自训练集文章。",
        "- 排序优先依据当前 A 类规则和低风险模式信号，不替代人工判断。",
        "- 若新增文章后再次运行脚本，此文件会自动刷新。",
        "",
    ]

    def add_item_section(title: str, ranked_items: list[ContentItem], reason_fn) -> None:
        lines.extend([f"## {title}", ""])
        for it in ranked_items:
            reason = reason_fn(it)
            lines.append(f"- [{it.title}](file://{it.path})：{reason}")
        if not ranked_items:
            lines.append("- 暂无候选。")
        lines.append("")

    add_item_section(
        "标题 DNA 候选",
        title_ranked,
        lambda it: f"标题同时具备场景/对象/冲突/判断等抓手，适合复核是否进入标题典型样本。当前标题：`{it.title}`",
    )
    add_item_section(
        "开头 DNA 候选",
        opening_ranked,
        lambda it: (
            f"开头前 300 字命中场景/故事/判断信号较多，摘录："
            f"`{select_representative_excerpt(it, ['故事', '剧场', '孩子', '母亲', '冲突'], fallback_limit=220, max_paragraphs=4)}`"
        ),
    )
    add_item_section(
        "结构 DNA 候选",
        structure_ranked,
        lambda it: f"结构代理信号较强：小标题 {len(it.subheadings)} 个，观点候选 {len(extract_claim_candidates(it.paragraphs))} 条。",
    )
    add_item_section(
        "词汇 DNA 候选",
        vocab_ranked,
        lambda it: (
            f"概念实词与判断词命中较高，适合补“概念栈/推进器”样本。摘要："
            f"`{select_representative_excerpt(it, CONTENT_TERMS + JUDGMENT_TERMS, fallback_limit=220)}`"
        ),
    )

    def add_para_section(title: str, ranked_paras: list[tuple[int, ContentItem, str]], why: str) -> None:
        lines.extend([f"## {title}", ""])
        for score, it, para in ranked_paras:
            lines.append(f"- [{it.title}](file://{it.path})：得分 {score}；{why} 摘录：`{normalize_candidate_excerpt(para)}`")
        if not ranked_paras:
            lines.append("- 暂无候选。")
        lines.append("")

    add_para_section("句法 DNA 候选", syntax_ranked, "具备提问/对照/转折/判断等句法信号")
    add_para_section("观点 DNA 候选", viewpoint_ranked, "具备重定义/强判断/核心议题词")
    add_para_section("案例 DNA 候选", case_ranked, "人物、场景、动作或冲突信号较完整")
    add_para_section("情绪 DNA 候选", emotion_ranked, "同时出现安抚/判断/情绪信号，适合复核情绪边界")
    return "\n".join(lines) + "\n"


def build_model_retest_candidates(root: Path, holdout: list[ContentItem], validation_report_text: str) -> str:
    already_used: set[str] = set()
    for it in holdout:
        if it.title in validation_report_text:
            already_used.add(str(it.path))

    scored: list[tuple[int, list[str], ContentItem, str]] = []
    for it in holdout:
        text = "\n".join(it.paragraphs)
        matched: list[tuple[str, int]] = []
        for model_name, cues in MODEL_CUES.items():
            score = count_term_hits(text, cues)
            if score > 0:
                matched.append((model_name, score))
        matched.sort(key=lambda x: x[1], reverse=True)
        if not matched:
            continue
        best_models = [name for name, _ in matched[:2]]
        best_score = sum(score for _, score in matched[:2])
        priority_bonus = 0 if str(it.path) in already_used else 5
        preferred_terms: list[str] = []
        for model_name in best_models:
            preferred_terms.extend(MODEL_CUES[model_name])
        reason = select_representative_excerpt(it, preferred_terms, fallback_limit=260)
        scored.append((best_score + priority_bonus, best_models, it, reason))

    scored.sort(key=lambda x: x[0], reverse=True)
    lines = [
        "# beliefs/models 复测候选",
        "",
        "用途：为 `beliefs_models.md` 和 `validation_report.md` 提供下一轮优先复测文章建议。",
        "",
        "说明：",
        "- 候选优先来自 holdout。",
        "- 已在 `validation_report.md` 明确使用过的文章会降权，未复测文章优先。",
        "- 模型建议基于低风险关键词命中，只作为人工复测入口。",
        "",
        "## 候选列表",
        "",
    ]
    if not scored:
        lines.append("- 暂无候选。")
    for score, models, it, reason in scored[:8]:
        reused_flag = "已在 validation_report 使用过" if str(it.path) in already_used else "未在 validation_report 复测"
        lines.append(
            f"- [{it.title}](file://{it.path})：优先级 {score}；建议复测模型 `{ ' / '.join(models) }`；{reused_flag}；摘要：`{reason}`"
        )
    lines.extend(
        [
            "",
            "## 建议使用方式",
            "",
            "- 月度重更新时，从前 2-3 篇里选样补进 `validation_report.md`。",
            "- 若某篇与已有模型不够匹配，也可以把它当“边界/反例候选”，用于修正模型定义。",
        ]
    )
    return "\n".join(lines) + "\n"


def replace_marked_block(text: str, marker: str, content: str) -> str:
    pattern = re.compile(
        rf"(<!-- AUTO:{re.escape(marker)}_START -->\n)(.*?)(\n<!-- AUTO:{re.escape(marker)}_END -->)",
        re.S,
    )
    return pattern.sub(rf"\1{content}\3", text)


def format_pct(rate: float, digits: int = 1) -> str:
    return f"{rate * 100:.{digits}f}%"


def format_num(value: float, digits: int = 1) -> str:
    return f"{value:.{digits}f}"


def format_count_pairs(pairs: list[tuple[str, int]] | list[list[Any]], limit: int = 5) -> str:
    rendered: list[str] = []
    for item in list(pairs)[:limit]:
        name, count = item[0], item[1]
        rendered.append(f"{name} {count}")
    return "、".join(rendered) if rendered else "待统计"


def render_corpus_overview(summary: dict[str, Any], corpus: str, holdout_ratio: float) -> str:
    return (
        f"语料范围：`docs/{corpus}` 共 {summary['total']} 篇；"
        f"按主题分层抽取 {int(round(holdout_ratio * 100))}% 作为验证集；"
        f"本基线基于训练集 {summary['train']} 篇统计生成。  "
    )


def render_title_a_class(summary: dict[str, Any]) -> str:
    tm = summary["title_metrics"]
    length = tm["length"]
    sentence_types = tm.get("sentence_types", {})
    total = int(length.get("count", 0)) or 1
    return "\n".join(
        [
            f"- 平均标题字数：{format_num(length['mean'], 1)} 字；分位区间 P25={length['p25']}，P50={length['p50']}，P75={length['p75']}",
            "- 标题句式占比："
            f"陈述句 {sentence_types.get('statement', 0)}/{total}，"
            f"判断句 {sentence_types.get('judgment', 0)}/{total}，"
            f"疑问句 {sentence_types.get('question', 0)}/{total}，"
            f"感叹句 {sentence_types.get('exclamation', 0)}/{total}，"
            f"命令句 {sentence_types.get('command', 0)}/{total}",
            f"- 是否前置结论：{format_pct(tm['front_conclusion_rate'])}",
            f"- 是否制造冲突：{format_pct(tm['conflict_rate'])}",
            f"- 是否使用数字：{format_pct(tm['digit_rate'])}",
            f"- 对象词命中率：{format_pct(tm['object_word_rate'])}",
            f"- 场景词命中率：{format_pct(tm['scene_word_rate'])}",
            f"- 强情绪词命中率：{format_pct(tm['emotion_word_rate'])}",
        ]
    )


def render_opening_a_class(summary: dict[str, Any]) -> str:
    om = summary["opening_metrics"]
    position = om.get("core_judgment_char_position", {})
    if position:
        position_line = (
            f"- 核心判断出现位置：在已命中样本中，首个核心判断信号平均出现在前 {format_num(position['mean'], 1)} 字；"
            f"P25={position['p25']}，P50={position['p50']}，P75={position['p75']}；当前命中样本仅 {position['count']}/{summary['train']}"
        )
    else:
        position_line = "- 核心判断出现位置：待统计"
    qstats = om["question_count_in_first_300_chars"]
    return "\n".join(
        [
            "- 开头前 100/300 字节奏：程序口径上更常见“场景/故事先行”，详见下列命中率",
            position_line,
            f"- 是否先给结论：{format_pct(om['has_conclusion_rate'])}",
            f"- 是否从误区切入：{format_pct(om['misconception_open_rate'])}",
            f"- 是否从场景切入：{format_pct(om['scene_open_rate'])}",
            f"- 是否从故事切入：{format_pct(om['story_open_rate'])}",
            f"- 开头问题句数量：前 300 字平均 {format_num(qstats['mean'], 2)} 个；P25={qstats['p25']}，P50={qstats['p50']}，P75={qstats['p75']}",
            "- 前 300 字废话比例：本轮不做程序统计",
            "- 进入主题速度：从规则命中看，明显偏“场景/故事带入后再推进”，而非直接结论先行",
        ]
    )


def render_syntax_a_class(summary: dict[str, Any], corpus: str) -> str:
    sm = summary["style_metrics"]
    sl = sm["sentence_length"]
    return "\n".join(
        [
            f"数据来源：`outputs/{corpus}/corpus_summary.json` 的 `style_metrics`。",
            "",
            "#### 4.1 句长与段落节奏",
            "",
            f"- 句长均值：约 {format_num(sl['mean'], 1)} 字/句",
            f"- 句长分位区间：P25={sl['p25']}，P50={sl['p50']}，P75={sl['p75']}",
            f"- 样本句数：{sl['count']}",
            "- 长短句比例：待统计",
            "- 段落平均长度：待统计",
            "- 单句段比例：待统计",
            "",
            "#### 4.2 句式与语气信号（训练集总计）",
            "",
            f"- 疑问句/问号：{sm['question_marks']}",
            f"- 祈使/指令信号（“你要/不要/别/请/务必/必须”）：{sm['imperative_signals']}",
            f"- 转折信号（“但是/然而/不过/但”）：{sm['turn_signals']}",
            f"- 因果信号（“因为/所以/因此”）：{sm['causal_signals']}",
            f"- 第一人称（“我/我们”）：{sm['first_person_tokens']}",
            f"- 第二人称（“你/你们”）：{sm['second_person_tokens']}",
            f"- 确定性（“一定/显然/必须/肯定”）：{sm['certainty_tokens']}",
            f"- 谨慎性（“可能/也许/大概/或许”）：{sm['hedge_tokens']}",
            f"- 类比/比喻信号（“像/如同/仿佛/就像/好比”）：{sm['analogy_tokens']}",
            "- 反问句比例：待统计",
            "- 判断句比例：待统计",
            "- 否定句比例：待统计",
            "- 排比句比例：待统计",
            "- 句式指纹命中率：待统计",
        ]
    )


def render_structure_a_class(summary: dict[str, Any]) -> str:
    stm = summary["structure_metrics"]
    subheading_count = stm["subheading_count"]
    subheading_length = stm["subheading_length"]
    depth = stm.get("depth", {})
    bucket = stm["case_bucket_distribution"]
    lines = [
        (
            f"- 小标题数量：平均 {format_num(subheading_count['mean'], 1)} 个；"
            f"P25={subheading_count['p25']}，P50={subheading_count['p50']}，P75={subheading_count['p75']}"
            if subheading_count
            else "- 小标题数量：待统计"
        ),
        f"- 小标题文章覆盖率：{format_pct(stm['subheading_article_rate'])}",
        (
            f"- 小标题平均长度：{format_num(subheading_length['mean'], 1)} 字；"
            f"P25={subheading_length['p25']}，P50={subheading_length['p50']}，P75={subheading_length['p75']}"
            if subheading_length
            else "- 小标题平均长度：待统计"
        ),
        "- 结构路径类型占比：待统计",
        f"- 每 500 字明确观点数量：{stm['claim_count_per_500_chars']}",
        f"- 案例分布位置：前段 {format_pct(bucket['front'])}，中段 {format_pct(bucket['middle'])}，后段 {format_pct(bucket['tail'])}",
        "- 方法论分布位置：待统计",
        f"- 转折频率：{stm['turn_signals_per_1000_chars']} / 千字",
        f"- 是否总分总：待统计（当前可用代理：结尾总结命中率 {format_pct(stm['tail_summary_rate'])}）",
    ]
    if depth:
        lines.append(
            f"- 层级深度：平均 {format_num(depth['mean'], 1)} 层；P25={depth['p25']}，P50={depth['p50']}，P75={depth['p75']}"
        )
    else:
        lines.append("- 层级深度：待统计")
    lines.extend(
        [
            f"- 结尾是否总结：{format_pct(stm['tail_summary_rate'])}",
            f"- 是否给行动建议：{format_pct(stm['tail_action_rate'])}",
            f"- 是否商业转化：{format_pct(stm['tail_cta_rate'])}",
        ]
    )
    return "\n".join(lines)


def render_vocab_a_class(summary: dict[str, Any]) -> str:
    vm = summary["vocab_metrics"]

    def pair_line(label: str, pairs: list[list[Any]] | list[tuple[str, int]], limit: int = 8) -> str:
        return f"- {label}：{format_count_pairs(pairs, limit=limit)}"

    lines = [
        pair_line("高频实词", vm["top_content_words"], limit=10),
        pair_line("高频连接词", vm["top_connectors"], limit=8),
        pair_line("高频判断词", vm["top_judgment_words"], limit=8),
        pair_line("高频对象词", vm["top_object_words"], limit=8),
        pair_line("高频场景词", vm["top_scene_words"], limit=8),
    ]
    if vm["forbidden_hit_count"] > 0:
        lines.append(
            f"- 禁用词命中率：{vm['forbidden_hit_per_1000_chars']} / 千字；命中项为 {format_count_pairs(vm['forbidden_words'], limit=8)}"
        )
    else:
        lines.append("- 禁用词命中率：0 / 千字（当前训练集未命中既定禁用词表）")
    return "\n".join(lines)


def render_viewpoint_a_class(summary: dict[str, Any]) -> str:
    vm = summary["viewpoint_metrics"]
    total_judgment = vm["strong_judgment_count"] + vm["hedge_count"]
    return "\n".join(
        [
            f"- 每 500 字观点数量：{vm['claim_count_per_500_chars']}",
            f"- 强判断比例：{format_pct(vm['strong_judgment_ratio'], 2)}（{vm['strong_judgment_count']} 个强判断信号 / {total_judgment} 个强判断与谨慎信号总和）",
            f"- 谨慎表达比例：{format_pct(vm['hedge_ratio'], 2)}",
            "- 反常识句数量：待统计",
            "- 问题重定义次数：不做程序硬统计，保留给 LLM/人工判断",
            "- 否定对象出现频率：待统计",
            "- 判断标准数量：待统计",
            "- 解决方案密度：待统计",
        ]
    )


def render_case_a_class(summary: dict[str, Any]) -> str:
    cm = summary["case_metrics"]
    length = cm["case_paragraph_length"]
    return "\n".join(
        [
            f"- 每 1000 字案例数量：{cm['case_paragraphs_per_1000_chars']}（按案例段落数统计）",
            f"- 案例长度：平均 {format_num(length['mean'], 1)} 字；P25={length['p25']}，P50={length['p50']}，P75={length['p75']}",
            "- 案例来源分布：本轮未细分“自述/采访/创排/角色故事”等来源类型",
            f"- 案例角色分布：高频角色为{format_count_pairs(cm['top_roles'], limit=5)}",
            f"- 案例场景分布：高频场景为{format_count_pairs(cm['top_scenes'], limit=6)}",
            f"- 比喻使用率：{cm['analogy_per_1000_chars']} / 千字",
            "- 类比类型分布：待统计",
        ]
    )


def render_emotion_a_class(summary: dict[str, Any]) -> str:
    em = summary["emotion_metrics"]
    return "\n".join(
        [
            f"- 强情绪词频：{em['strong_emotion_per_1000_chars']} / 千字；高频词为 {format_count_pairs(em['strong_emotion_words'], limit=8)}",
            "- 吐槽词频：本轮不做程序统计，保留给 LLM/人工判断",
            f"- 否定句频：{em['negation_per_1000_chars']} / 千字（按“不/没/无/别/不要/不能/不是”等否定信号近似统计）",
            f"- 安抚句频：{em['comfort_per_1000_chars']} / 千字；高频安抚词为 {format_count_pairs(em['comfort_words'], limit=8)}",
            f"- 权威判断句频：{em['authority_per_1000_chars']} / 千字；高频权威词为 {format_count_pairs(em['authority_words'], limit=8)}",
            "- 是否攻击具体人：本轮不做程序统计，保留给 LLM/人工判断",
            f"- 是否制造焦虑：{em['anxiety_per_1000_chars']} / 千字；高频焦虑触发词为 {format_count_pairs(em['anxiety_words'], limit=8)}",
        ]
    )


def sync_style_dna(out_dir: Path, summary: dict[str, Any], corpus: str, holdout_ratio: float) -> None:
    style_dna_path = out_dir / "style_dna.md"
    if not style_dna_path.exists():
        return
    text = style_dna_path.read_text(encoding="utf-8")
    replacements = {
        "CORPUS_OVERVIEW": render_corpus_overview(summary, corpus, holdout_ratio),
        "TITLE_A_CLASS": render_title_a_class(summary),
        "OPENING_A_CLASS": render_opening_a_class(summary),
        "STRUCTURE_A_CLASS": render_structure_a_class(summary),
        "SYNTAX_A_CLASS": render_syntax_a_class(summary, corpus),
        "VOCAB_A_CLASS": render_vocab_a_class(summary),
        "VIEWPOINT_A_CLASS": render_viewpoint_a_class(summary),
        "CASE_A_CLASS": render_case_a_class(summary),
        "EMOTION_A_CLASS": render_emotion_a_class(summary),
    }
    updated = text
    for marker, content in replacements.items():
        updated = replace_marked_block(updated, marker, content)
    if updated != text:
        style_dna_path.write_text(updated, encoding="utf-8")


def main() -> None:
    args = parse_args()
    docs_dir = args.docs_dir or (ROOT / "docs" / args.corpus)
    out_dir = args.out_dir or (ROOT / "outputs" / args.corpus)
    state_dir, generated_dir = ensure_dirs(out_dir)

    manifest_path = state_dir / "manifest.json"
    review_queue_path = state_dir / "review_queue.md"
    changelog_path = state_dir / "changelog.md"
    previous_manifest = load_json(manifest_path)
    previous_summary = load_json(out_dir / "corpus_summary.json")
    validation_report_text = (out_dir / "validation_report.md").read_text(encoding="utf-8") if (out_dir / "validation_report.md").exists() else ""

    items = build_items(docs_dir=docs_dir, root=ROOT, previous_manifest=previous_manifest)
    raise_on_changed_title_duplicates(items, ROOT)
    train, holdout = stratified_holdout(items, ratio=args.holdout_ratio)

    holdout_set = {it.path for it in holdout}
    train_set = {it.path for it in train}

    index_path = out_dir / "content_index.jsonl"
    with index_path.open("w", encoding="utf-8") as f:
        for i, it in enumerate(items, start=1):
            f.write(
                json.dumps(
                    {
                        "content_id": it.content_id,
                        "file": str(it.path.relative_to(ROOT)),
                        "title": it.title,
                        "account": it.account,
                        "published_at": it.published_at,
                        "url": it.url,
                        "topic": it.topic,
                        "paragraph_count": len(it.paragraphs),
                        "body": it.body,
                        "status": it.status,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    holdout_list_path = out_dir / "holdout_list.md"
    by_topic_holdout: dict[str, list[ContentItem]] = defaultdict(list)
    for it in holdout:
        by_topic_holdout[it.topic].append(it)

    with holdout_list_path.open("w", encoding="utf-8") as f:
        f.write("# Holdout（验证集）清单：按主题分层抽取 20%\n\n")
        for topic in sorted(by_topic_holdout.keys()):
            f.write(f"## {topic}\n\n")
            for it in sorted(by_topic_holdout[topic], key=lambda x: x.published_at or x.path.stem):
                rel = it.path.relative_to(ROOT)
                f.write(f"- {it.published_at or ''} [{it.title}](file://{it.path}) ({rel})\n")
            f.write("\n")
        f.write(f"\n---\n\n训练集：{len(train)} 篇；验证集：{len(holdout)} 篇；总计：{len(items)} 篇。\n")

    claim_path = out_dir / "claim_candidates.jsonl"
    with claim_path.open("w", encoding="utf-8") as f:
        for it in train:
            cands = extract_claim_candidates(it.paragraphs)
            for c in cands:
                f.write(
                    json.dumps(
                        {
                            "file": str(it.path.relative_to(ROOT)),
                            "title": it.title,
                            "topic": it.topic,
                            "published_at": it.published_at,
                            "para_index": c["para_index"],
                            "signals": c["signals"],
                            "text": c["text"],
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )

    metrics = compute_style_metrics(train)
    title_metrics = compute_title_metrics(train)
    opening_metrics = compute_opening_metrics(train)
    viewpoint_metrics = compute_viewpoint_metrics(train)
    case_metrics = compute_case_metrics(train)
    structure_metrics = compute_structure_metrics(train, metrics, viewpoint_metrics)
    vocab_metrics = compute_vocab_metrics(train)
    emotion_metrics = compute_emotion_metrics(train)
    kw = top_keywords(train)
    summary_payload = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "corpus": args.corpus,
        "total": len(items),
        "train": len(train),
        "holdout": len(holdout),
        "topics": dict(Counter([it.topic for it in items])),
        "style_metrics": metrics,
        "title_metrics": title_metrics,
        "opening_metrics": opening_metrics,
        "structure_metrics": structure_metrics,
        "viewpoint_metrics": viewpoint_metrics,
        "case_metrics": case_metrics,
        "vocab_metrics": vocab_metrics,
        "emotion_metrics": emotion_metrics,
        "top_keywords": kw,
    }
    summary_path = out_dir / "corpus_summary.json"
    write_json(summary_path, summary_payload)

    manifest_payload = {
        "generated_at": summary_payload["generated_at"],
        "corpus": args.corpus,
        "docs_dir": str(docs_dir.relative_to(ROOT)),
        "out_dir": str(out_dir.relative_to(ROOT)),
        "holdout_ratio": args.holdout_ratio,
        "items": [
            {
                **summarize_item(it, ROOT),
                "split": "holdout" if it.path in holdout_set else "train" if it.path in train_set else "unknown",
            }
            for it in items
        ],
    }
    write_json(manifest_path, manifest_payload)

    review_text = build_review_queue(
        corpus=args.corpus,
        root=ROOT,
        out_dir=out_dir,
        items=items,
        train=train,
        holdout=holdout,
        previous_manifest=previous_manifest,
        previous_summary=previous_summary,
        current_summary=summary_payload,
    )
    sync_style_dna(out_dir, summary_payload, args.corpus, args.holdout_ratio)
    review_queue_path.write_text(review_text, encoding="utf-8")
    append_changelog(changelog_path, items, summary_payload)
    (generated_dir / "typical_sample_candidates.md").write_text(
        build_typical_sample_candidates(ROOT, train),
        encoding="utf-8",
    )
    (generated_dir / "model_retest_candidates.md").write_text(
        build_model_retest_candidates(ROOT, holdout, validation_report_text),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
