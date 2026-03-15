import argparse
import traceback

import torch

try:
    from funasr import AutoModel
except ImportError as exc:
    raise ImportError(
        "无法导入 funasr.AutoModel，请先确认当前环境已按项目要求安装 FunASR。"
    ) from exc

try:
    from funasr.utils.postprocess_utils import rich_transcription_postprocess
except ImportError as exc:
    raise ImportError(
        "无法导入 rich_transcription_postprocess，请确认当前 FunASR 版本可用。"
    ) from exc


def parse_args():
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="对单个中文音频执行 SenseVoice 冒烟测试，并打印原始结果与清洗结果。"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="待测试的音频文件路径",
    )
    return parser.parse_args()


def choose_device():
    """自动选择推理设备。"""
    if torch.cuda.is_available():
        return "cuda:0"
    return "cpu"


def load_sensevoice_model(device):
    """加载 SenseVoice 模型和 VAD。"""
    return AutoModel(
        model="iic/SenseVoiceSmall",
        vad_model="fsmn-vad",
        vad_kwargs={"max_single_segment_time": 30000},
        device=device,
    )


def get_raw_text_from_result(result):
    """从模型返回结果中提取第一条文本。"""
    if not result:
        return ""

    first_item = result[0]
    if not isinstance(first_item, dict):
        return ""

    text = first_item.get("text", "")
    if text is None:
        return ""
    return str(text)


def run_smoke_test(input_path):
    """执行一次简单的 SenseVoice 识别测试。"""
    device = choose_device()

    print(f"current device: {device}")
    print(f"current input file: {input_path}")

    model = load_sensevoice_model(device)

    result = model.generate(
        input=input_path,
        cache={},
        language="zh",
        use_itn=True,
        batch_size_s=60,
        merge_vad=True,
        merge_length_s=15,
    )

    print("raw result:")
    print(result)

    if not result:
        print("raw text:")
        print("(empty result)")
        print("clean text:")
        print("(empty result)")
        print("提示：模型返回结果为空，请检查音频内容、路径或模型加载状态。")
        return

    raw_text = get_raw_text_from_result(result)

    print("raw text:")
    print(raw_text if raw_text else "(text field is empty)")

    clean_text = ""
    if raw_text:
        clean_text = rich_transcription_postprocess(raw_text)

    print("clean text:")
    print(clean_text if clean_text else "(clean text is empty)")


def main():
    """程序入口。"""
    args = parse_args()

    try:
        run_smoke_test(args.input)
    except Exception:
        print("程序执行失败，完整异常如下：")
        traceback.print_exc()


if __name__ == "__main__":
    main()
