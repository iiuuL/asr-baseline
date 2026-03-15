import re
from pathlib import Path

TAG_PATTERN = re.compile(r"<\|.*?\|>")


def clean_ref_tsv(ref_path: Path) -> None:
    # 全程显式使用 utf-8，避免编码歧义。
    lines = ref_path.read_text(encoding="utf-8").splitlines()
    output_lines = []

    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue

        parts = line.split("\t", 1)
        if len(parts) != 2:
            raise ValueError(
                f"TSV 格式错误: {ref_path} 第 {line_number} 行不是 'utt_id<TAB>text'"
            )

        utt_id = parts[0].strip()
        text = parts[1]
        cleaned_text = TAG_PATTERN.sub("", text)
        output_lines.append(f"{utt_id}\t{cleaned_text}")

    # 覆盖写回原文件。
    ref_path.write_text("\n".join(output_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    target = Path("data/eval/ref.tsv")
    clean_ref_tsv(target)
    print(f"cleaned: {target}")
