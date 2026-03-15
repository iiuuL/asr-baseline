import argparse
import json
import time
import traceback
from typing import Any, Dict

try:
    import torch
except ImportError:
    torch = None

try:
    from funasr import AutoModel
except ImportError:
    AutoModel = None

try:
    from asr_core.tag_parser import normalize_whitespace, parse_metadata, strip_emojis, strip_tags
except ImportError:
    # 兼容直接执行：python .\asr_core\engine.py
    from tag_parser import normalize_whitespace, parse_metadata, strip_emojis, strip_tags


class InferenceEngine:
    """服务版和评测版共享的推理核心。"""

    def __init__(self):
        # 模型基础配置
        self.model_name = "iic/SenseVoiceSmall"
        self.vad_model_name = "fsmn-vad"

        # 默认推理参数
        self.default_language = "zh"
        self.default_use_itn = True
        self.default_batch_size_s = 60
        self.default_merge_vad = True
        self.default_merge_length_s = 15

        # 设备自动选择
        self.device = self._choose_device()

        # 模型对象只在初始化阶段加载一次
        self.model = None
        self._model_load_error = None
        self._load_model_once()

    def _choose_device(self) -> str:
        """自动选择设备：优先 CUDA，不可用则 CPU。"""
        try:
            if torch is not None and torch.cuda.is_available():
                return "cuda:0"
        except Exception:
            traceback.print_exc()
        return "cpu"

    def _load_model_once(self) -> None:
        """初始化阶段加载一次模型。"""
        if self.model is not None:
            return

        try:
            if AutoModel is None:
                raise ImportError("无法导入 funasr.AutoModel，请确认环境已安装 FunASR。")

            self.model = AutoModel(
                model=self.model_name,
                vad_model=self.vad_model_name,
                vad_kwargs={"max_single_segment_time": 30000},
                device=self.device,
            )
        except Exception as error:
            self._model_load_error = str(error)
            self.model = None
            traceback.print_exc()

    @staticmethod
    def _extract_raw_text(raw_result: Any) -> str:
        """尽量从模型原始输出中提取 text 字段。"""
        if not raw_result:
            return ""

        if isinstance(raw_result, list) and raw_result:
            first_item = raw_result[0]
            if isinstance(first_item, dict):
                value = first_item.get("text", "")
                return "" if value is None else str(value)

        if isinstance(raw_result, dict):
            value = raw_result.get("text", "")
            return "" if value is None else str(value)

        return ""

    @staticmethod
    def _extract_timestamp(raw_result: Any) -> Any:
        """尽量提取时间戳字段。"""
        if not raw_result:
            return None

        candidate_keys = ("timestamp", "timestamps", "time_stamp", "time_stamps")

        if isinstance(raw_result, list) and raw_result:
            first_item = raw_result[0]
            if isinstance(first_item, dict):
                for key in candidate_keys:
                    if key in first_item:
                        return first_item[key]

        if isinstance(raw_result, dict):
            for key in candidate_keys:
                if key in raw_result:
                    return raw_result[key]

        return None

    def transcribe_file(
        self,
        audio_path: str,
        language: str = "zh",
        use_itn: bool = True,
    ) -> Dict[str, Any]:
        """识别单个音频并返回结构化结果。"""
        start_time = time.perf_counter()

        payload: Dict[str, Any] = {
            "ok": False,
            "raw_result": None,
            "raw_text": "",
            "text": "",
            "text_clean": "",
            "metadata": {},
            "language": language,
            "device": self.device,
            "elapsed_ms": 0.0,
            "timestamp": None,
        }

        try:
            if self.model is None:
                raise RuntimeError(self._model_load_error or "模型未加载成功，无法推理。")

            raw_result = self.model.generate(
                input=audio_path,
                cache={},
                language=language,
                use_itn=use_itn,
                batch_size_s=self.default_batch_size_s,
                merge_vad=self.default_merge_vad,
                merge_length_s=self.default_merge_length_s,
            )

            raw_text = self._extract_raw_text(raw_result)
            timestamp = self._extract_timestamp(raw_result)

            # metadata 直接基于原始标签文本解析，避免丢标签。
            metadata = parse_metadata(raw_text)

            # 按新规则：text 直接走纯净清洗链路。
            pure_text = strip_tags(raw_text)
            pure_text = strip_emojis(pure_text)
            pure_text = normalize_whitespace(pure_text)

            payload.update(
                {
                    "ok": True,
                    "raw_result": raw_result,
                    "raw_text": raw_text,
                    "text": pure_text,
                    "text_clean": pure_text,
                    "metadata": metadata,
                    "timestamp": timestamp,
                }
            )
        except Exception as error:
            traceback.print_exc()
            payload["ok"] = False
            payload["error"] = str(error)
        finally:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            payload["elapsed_ms"] = round(elapsed_ms, 3)

        return payload

    def get_status(self) -> Dict[str, Any]:
        """返回引擎状态。"""
        return {
            "model_loaded": self.model is not None,
            "device": self.device,
            "model_name": self.model_name,
            "vad_model_name": self.vad_model_name,
        }


def _parse_args():
    """命令行参数解析。"""
    parser = argparse.ArgumentParser(description="InferenceEngine 单文件测试入口")
    parser.add_argument("--input", required=True, help="音频文件路径")
    parser.add_argument("--language", default="zh", help="语言参数，默认 zh")
    parser.add_argument("--use_itn", type=int, default=1, help="是否使用 ITN，1 表示 True，0 表示 False")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()

    engine = InferenceEngine()
    result = engine.transcribe_file(
        audio_path=args.input,
        language=args.language,
        use_itn=bool(args.use_itn),
    )

    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
