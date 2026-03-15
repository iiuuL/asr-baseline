import argparse
import traceback
from datetime import datetime
from pathlib import Path

# 只复用共享推理核心，不重复写模型加载逻辑。
try:
    from asr_core.engine import InferenceEngine
except ImportError:
    # 兼容从 scripts 目录直接执行时的导入路径。
    import sys

    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    from asr_core.engine import InferenceEngine


SUPPORTED_EXTENSIONS = {".wav", ".mp3", ".flac", ".m4a"}
ERROR_LOG_PATH = Path("logs") / "eval_batch_errors.log"


def parse_bool(value: str) -> bool:
    """把命令行字符串转换为布尔值，便于新手使用 true/false。"""
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y", "on"}:
        return True
    if text in {"false", "0", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError("--use_itn 仅支持 true/false（或 1/0）")


def parse_args():
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(description="批量识别目录音频并输出 pred.tsv")
    parser.add_argument("--input_dir", required=True, help="音频目录（必填）")
    parser.add_argument("--output_tsv", required=True, help="输出 TSV 文件路径（必填）")
    parser.add_argument("--language", default="zh", help="语言参数，默认 zh")
    parser.add_argument(
        "--use_itn",
        type=parse_bool,
        default=True,
        help="是否使用 ITN，默认 true，可填 true/false",
    )
    return parser.parse_args()


def collect_audio_files(input_dir: Path) -> list[Path]:
    """收集目录下支持扩展名的音频文件，并按文件名排序保证结果可复现。"""
    audio_files = []
    for path in input_dir.iterdir():
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            audio_files.append(path)
    audio_files.sort(key=lambda item: item.name.lower())
    return audio_files


def append_error_log(audio_path: Path, message: str, tb_text: str = ""):
    """把单个文件错误追加写入日志。"""
    ERROR_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with ERROR_LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(f"[{current_time}] file: {audio_path}\n")
        log_file.write(f"message: {message}\n")
        if tb_text:
            log_file.write(tb_text)
            if not tb_text.endswith("\n"):
                log_file.write("\n")
        log_file.write("\n")


def write_tsv(output_tsv: Path, rows: list[tuple[str, str]]):
    """将识别结果写入 TSV：utt_id<TAB>pred_text。"""
    output_tsv.parent.mkdir(parents=True, exist_ok=True)
    with output_tsv.open("w", encoding="utf-8", newline="") as file:
        for utt_id, pred_text in rows:
            safe_text = str(pred_text).replace("\t", " ").replace("\r", " ").replace("\n", " ")
            file.write(f"{utt_id}\t{safe_text}\n")


def run_batch(input_dir: Path, output_tsv: Path, language: str, use_itn: bool):
    """执行批量识别流程。"""
    if not input_dir.exists():
        raise FileNotFoundError(f"输入目录不存在: {input_dir}")
    if not input_dir.is_dir():
        raise NotADirectoryError(f"输入路径不是目录: {input_dir}")

    audio_files = collect_audio_files(input_dir)
    if not audio_files:
        print("未找到可处理的音频文件（仅支持 .wav .mp3 .flac .m4a）")
        write_tsv(output_tsv, [])
        return

    engine = InferenceEngine()
    rows: list[tuple[str, str]] = []
    total = len(audio_files)

    for index, audio_path in enumerate(audio_files, start=1):
        print(f"[{index}/{total}] processing {audio_path.name}")

        try:
            result = engine.transcribe_file(
                audio_path=str(audio_path),
                language=language,
                use_itn=use_itn,
            )

            # 按要求：pred_text 必须写 result["text"]。
            pred_text = str(result.get("text", ""))
            rows.append((audio_path.stem, pred_text))

            # 引擎内部失败时也记录日志，但不终止程序。
            if not result.get("ok", False):
                error_message = str(result.get("error", "推理失败，未返回详细错误"))
                append_error_log(audio_path, error_message)

        except Exception as error:
            append_error_log(audio_path, str(error), traceback.format_exc())
            rows.append((audio_path.stem, ""))

    write_tsv(output_tsv, rows)
    print(f"done, saved to: {output_tsv}")


def main():
    """程序入口。"""
    args = parse_args()

    try:
        run_batch(
            input_dir=Path(args.input_dir),
            output_tsv=Path(args.output_tsv),
            language=args.language,
            use_itn=args.use_itn,
        )
    except Exception:
        print("程序执行失败，完整异常如下：")
        traceback.print_exc()


if __name__ == "__main__":
    main()
