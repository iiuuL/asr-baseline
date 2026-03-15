import json
import re
from typing import Any

# 提取标签内容使用与需求一致的正则形式。
TAG_EXTRACT_PATTERN = r"<\|(.*?)\|>"
# 删除标签：匹配任意 <|...|> 结构，使用非贪婪模式避免跨段误匹配。
TAG_BLOCK_PATTERN = re.compile(r"<\|.*?\|>")

# Emoji 粗粒度覆盖范围（标准库 re 即可），用于评测文本清洗。
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F700-\U0001F77F"  # alchemical
    "\U0001F780-\U0001F7FF"  # geometric extended
    "\U0001F800-\U0001F8FF"  # arrows-c
    "\U0001F900-\U0001F9FF"  # supplemental symbols
    "\U0001FA00-\U0001FAFF"  # chess, symbols
    "\U00002700-\U000027BF"  # dingbats
    "\U00002600-\U000026FF"  # misc symbols
    "]+",
    flags=re.UNICODE,
)

# 支持的标签集合。
LANGUAGE_TAGS = {"zh", "en", "yue", "ja", "ko", "nospeech"}
EMOTION_TAGS = {
    "HAPPY",
    "SAD",
    "ANGRY",
    "NEUTRAL",
    "FEARFUL",
    "DISGUSTED",
    "SURPRISED",
}
EVENT_TAGS = {
    "speech": "Speech",
    "bgm": "BGM",
    "applause": "Applause",
    "laughter": "Laughter",
    "cry": "Cry",
    "sneeze": "Sneeze",
    "breath": "Breath",
    "cough": "Cough",
}
ITN_TAGS = {"withitn", "woitn"}


def extract_tags(text: str) -> list[str]:
    """
    提取所有 <|...|> 中的内容。

    例如：
    输入：<|zh|><|HAPPY|><|Speech|>今天天气真好。<|Laughter|>
    输出：["zh", "HAPPY", "Speech", "Laughter"]
    """
    if not text:
        return []

    return [item.strip() for item in re.findall(TAG_EXTRACT_PATTERN, text)]


def parse_metadata(text: str) -> dict[str, Any]:
    """
    根据标签生成 metadata 字段。

    返回字段：
    - language
    - emotion
    - events
    - has_speech
    - itn_mode
    - unknown_tags
    """
    tags = extract_tags(text)

    language = None
    emotion = None
    events: list[str] = []
    itn_mode = None
    unknown_tags: list[str] = []

    for raw_tag in tags:
        tag = raw_tag.strip()
        lower_tag = tag.lower()
        upper_tag = tag.upper()

        if lower_tag in LANGUAGE_TAGS:
            language = lower_tag
            continue

        if upper_tag in EMOTION_TAGS:
            emotion = upper_tag
            continue

        if lower_tag in EVENT_TAGS:
            event_name = EVENT_TAGS[lower_tag]
            if event_name not in events:
                events.append(event_name)
            continue

        if lower_tag in ITN_TAGS:
            itn_mode = lower_tag
            continue

        unknown_tags.append(tag)

    return {
        "language": language,
        "emotion": emotion,
        "events": events,
        "has_speech": "Speech" in events,
        "itn_mode": itn_mode,
        "unknown_tags": unknown_tags,
    }


def strip_tags(text: str) -> str:
    """删除所有 <|...|> 标签，仅保留文本主体。"""
    if not text:
        return ""

    return TAG_BLOCK_PATTERN.sub("", text)


def strip_emojis(text: str) -> str:
    """
    删除文本中的表情符号。

    该函数用于评测路径，避免 emoji 干扰指标计算。
    """
    if not text:
        return ""

    # 同时清理常见的变体选择符和连接符，避免残留不可见字符。
    cleaned = EMOJI_PATTERN.sub("", text)
    cleaned = cleaned.replace("\ufe0f", "").replace("\u200d", "")
    return cleaned


def normalize_whitespace(text: str) -> str:
    """合并多余空白，去除首尾空白。"""
    if not text:
        return ""

    # 先把常见全角空格和不间断空格标准化，再统一压缩空白。
    normalized = text.replace("\u3000", " ").replace("\xa0", " ")
    return re.sub(r"\s+", " ", normalized).strip()


def build_structured_output(raw_text: str) -> dict[str, Any]:
    """
    返回统一结构：
    {
      "raw_text": 原始文本,
      "text": 去标签并清理空白后的文本,
      "metadata": parse_metadata(raw_text)
    }
    """
    text_without_tags = strip_tags(raw_text)
    normalized_text = normalize_whitespace(text_without_tags)

    return {
        "raw_text": raw_text,
        "text": normalized_text,
        "metadata": parse_metadata(raw_text),
    }


if __name__ == "__main__":
    sample = "<|zh|><|SAD|><|Speech|> 今天   有点 难过 😢 。<|withitn|>"
    result = build_structured_output(sample)

    print("input:")
    print(sample)
    print("\nstructured output:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
