import argparse
import traceback
from datetime import datetime
from pathlib import Path

import torch

try:
    from funasr import AutoModel
except ImportError as exc:
    raise ImportError(
        "无法导入 funasr.AutoModel，请先确认当前环境已按项目要求安装 FunASR。"
    ) from exc


SUPPORTED_EXTENSIONS = {".wav", ".mp3", ".flac", ".m4a"}
ERROR_LOG_PATH = Path("logs") / "infer_errors.log"


def parse_args():
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="批量识别目录中的音频文件，并将结果保存为 TSV。"
    )
    parser.add_argument("--input_dir", required=True, help="待识别的音频目录")
    parser.add_argument("--output_tsv", required=True, help="输出 TSV 文件路径")
    return parser.parse_args()


def choose_device():
    """自动选择推理设备。"""
    if torch.cuda.is_available():
        return "cuda:0"
    return "cpu"


def load_sensevoice_model(device):
    """加载 SenseVoice 模型。"""
    return AutoModel(
        model="iic/SenseVoiceSmall",
        vad_model="fsmn-vad",
        vad_kwargs={"max_single_segment_time": 30000},
        device=device,
    )


def collect_audio_files(input_dir):
    """收集目录下支持的音频文件，并按文件名排序，方便复现结果。"""
    audio_files = []
    for path in input_dir.iterdir():
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            audio_files.append(path)
    audio_files.sort(key=lambda item: item.name.lower())
    return audio_files


def extract_text_from_result(result):
    """从模型输出中提取第一条文本。"""
    if not result:
        return ""

    first_item = result[0]
    if not isinstance(first_item, dict):
        return ""

    text = first_item.get("text", "")
    if text is None:
        return ""
    return str(text)


def append_error_log(audio_path, error):
    """将单个文件的错误信息追加写入日志。"""
    ERROR_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    time_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with ERROR_LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(f"[{time_text}] file: {audio_path}\n")
        log_file.write(traceback.format_exc())
        log_file.write("\n")


def infer_one_file(model, audio_path):
    """识别单个音频文件并返回文本。"""
    result = model.generate(
        input=str(audio_path),
        cache={},
        language="zh",
        use_itn=True,
        batch_size_s=60,
        merge_vad=True,
        merge_length_s=15,
    )
    return extract_text_from_result(result)


def write_tsv(output_tsv, rows):
    """将识别结果写入 TSV 文件。"""
    output_tsv.parent.mkdir(parents=True, exist_ok=True)
    with output_tsv.open("w", encoding="utf-8", newline="") as file:
        for utt_id, pred_text in rows:
            safe_text = pred_text.replace("\t", " ").replace("\r", " ").replace("\n", " ")
            file.write(f"{utt_id}\t{safe_text}\n")


def run_infer(input_dir, output_tsv):
    """执行目录批量识别。"""
    device = choose_device()
    print(f"current device: {device}")
    print(f"input dir: {input_dir}")
    print(f"output tsv: {output_tsv}")

    audio_files = collect_audio_files(input_dir)
    if not audio_files:
        print("未找到可处理的音频文件。支持扩展名：.wav .mp3 .flac .m4a")
        write_tsv(output_tsv, [])
        return

    model = load_sensevoice_model(device)
    rows = []
    total = len(audio_files)

    for index, audio_path in enumerate(audio_files, start=1):
        print(f"[{index}/{total}] processing {audio_path.name}")
        try:
            pred_text = infer_one_file(model, audio_path)
            rows.append((audio_path.stem, pred_text))
        except Exception as error:
            append_error_log(audio_path, error)
            print(f"识别失败，已记录到 {ERROR_LOG_PATH}: {audio_path.name}")

    write_tsv(output_tsv, rows)
    print(f"done, saved to: {output_tsv}")



def main():
    """程序入口。"""
    args = parse_args()
    input_dir = Path(args.input_dir)
    output_tsv = Path(args.output_tsv)

    try:
        if not input_dir.exists():
            raise FileNotFoundError(f"输入目录不存在: {input_dir}")
        if not input_dir.is_dir():
            raise NotADirectoryError(f"输入路径不是目录: {input_dir}")

        run_infer(input_dir, output_tsv)
    except Exception:
        print("程序执行失败，完整异常如下：")
        traceback.print_exc()


if __name__ == "__main__":
    main()
