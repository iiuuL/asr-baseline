import argparse
import json
import re
import traceback
import unicodedata
from pathlib import Path

try:
    from jiwer import wer
except ImportError as exc:
    raise ImportError(
        "无法导入 jiwer，请确认当前环境已按项目要求安装 jiwer。"
    ) from exc


METRICS_OUTPUT_PATH = Path("outputs") / "metrics.json"


def parse_args():
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="读取参考 TSV 和预测 TSV，计算 WER 和 SER。"
    )
    parser.add_argument("--ref_tsv", required=True, help="参考 TSV 文件路径")
    parser.add_argument("--pred_tsv", required=True, help="预测 TSV 文件路径")
    return parser.parse_args()


def read_tsv(tsv_path: Path):
    """读取 TSV 文件，返回 utt_id 到文本的映射。"""
    data = {}

    with tsv_path.open("r", encoding="utf-8") as file:
        for line_number, raw_line in enumerate(file, start=1):
            line = raw_line.rstrip("\n\r")
            if not line.strip():
                continue

            parts = line.split("\t", 1)
            if len(parts) != 2:
                raise ValueError(
                    f"TSV 格式错误: {tsv_path} 第 {line_number} 行不是 'utt_id<TAB>text'"
                )

            utt_id, text = parts[0].strip(), parts[1]
            if not utt_id:
                raise ValueError(
                    f"TSV 格式错误: {tsv_path} 第 {line_number} 行的 utt_id 为空"
                )

            data[utt_id] = text

    return data


def preprocess_for_distance(text: str) -> str:
    """
    评测预处理：
    1) 去除中英文标点
    2) 去除所有空白
    3) 转为小写
    """
    if text is None:
        return ""

    current = str(text).lower()

    # 使用 Unicode 类别过滤所有标点（中文和英文都覆盖）。
    current = "".join(ch for ch in current if not unicodedata.category(ch).startswith("P"))

    # 去除所有空白字符（空格、制表符、换行等）。
    current = re.sub(r"\s+", "", current)

    return current


def build_aligned_text_lists(ref_data, pred_data):
    """按 utt_id 对齐参考文本和预测文本。"""
    common_utt_ids = sorted(set(ref_data.keys()) & set(pred_data.keys()))
    ref_texts = []
    pred_texts = []

    for utt_id in common_utt_ids:
        ref_texts.append(ref_data[utt_id])
        pred_texts.append(pred_data[utt_id])

    return common_utt_ids, ref_texts, pred_texts


def calculate_ser(ref_texts, pred_texts):
    """计算句子错误率 SER。"""
    total_count = len(ref_texts)
    if total_count == 0:
        return 0.0

    sentence_error_count = 0
    for ref_text, pred_text in zip(ref_texts, pred_texts):
        if ref_text != pred_text:
            sentence_error_count += 1

    return sentence_error_count / total_count


def save_metrics(metrics):
    """将指标保存到固定位置 outputs/metrics.json。"""
    METRICS_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with METRICS_OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(metrics, file, ensure_ascii=False, indent=2)


def run_evaluation(ref_tsv: Path, pred_tsv: Path):
    """执行评测逻辑。"""
    ref_data = read_tsv(ref_tsv)
    pred_data = read_tsv(pred_tsv)

    ref_utt_ids = set(ref_data.keys())
    pred_utt_ids = set(pred_data.keys())
    missing_in_ref = sorted(pred_utt_ids - ref_utt_ids)
    missing_in_pred = sorted(ref_utt_ids - pred_utt_ids)

    common_utt_ids, ref_texts_raw, pred_texts_raw = build_aligned_text_lists(ref_data, pred_data)
    sample_count = len(common_utt_ids)

    # 在距离计算前做统一清洗。
    ref_texts = [preprocess_for_distance(text) for text in ref_texts_raw]
    pred_texts = [preprocess_for_distance(text) for text in pred_texts_raw]

    if sample_count == 0:
        wer_value = 0.0
        ser_value = 0.0
    else:
        wer_value = wer(ref_texts, pred_texts)
        ser_value = calculate_ser(ref_texts, pred_texts)

    metrics = {
        "num_eval_samples": sample_count,
        "num_missing_in_ref": len(missing_in_ref),
        "num_missing_in_pred": len(missing_in_pred),
        "wer": wer_value,
        "ser": ser_value,
        "metrics_output_path": str(METRICS_OUTPUT_PATH),
    }

    save_metrics(metrics)

    print(f"参与评测的样本数: {sample_count}")
    print(f"缺失于参考文件的 utt_id 数量: {len(missing_in_ref)}")
    print(f"缺失于预测文件的 utt_id 数量: {len(missing_in_pred)}")
    print(f"WER: {wer_value:.6f}")
    print(f"SER: {ser_value:.6f}")
    print(f"metrics saved to: {METRICS_OUTPUT_PATH}")


def main():
    """程序入口。"""
    args = parse_args()
    ref_tsv = Path(args.ref_tsv)
    pred_tsv = Path(args.pred_tsv)

    try:
        if not ref_tsv.exists():
            raise FileNotFoundError(f"参考 TSV 不存在: {ref_tsv}")
        if not pred_tsv.exists():
            raise FileNotFoundError(f"预测 TSV 不存在: {pred_tsv}")

        run_evaluation(ref_tsv, pred_tsv)
    except Exception:
        print("程序执行失败，完整异常如下：")
        traceback.print_exc()


if __name__ == "__main__":
    main()
