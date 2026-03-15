import os
import tempfile
import traceback
from contextlib import asynccontextmanager
from pathlib import Path
from threading import Lock
from typing import Any, Optional

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from asr_core.engine import InferenceEngine


# 全局引擎：服务启动时加载一次，避免每个请求重复加载模型。
ENGINE: Optional[InferenceEngine] = None

# 全局会话缓存：按 session_id 累积音频字节。
session_storage: dict[str, bytearray] = {}
# 并发保护锁，避免多个请求同时写同一会话产生竞争。
session_storage_lock = Lock()


def default_metadata() -> dict[str, Any]:
    """返回固定 metadata 结构，保证接口字段稳定。"""
    return {
        "language": None,
        "emotion": None,
        "events": [],
        "has_speech": False,
        "itn_mode": None,
        "unknown_tags": [],
    }


def normalize_metadata(raw_metadata: Any) -> dict[str, Any]:
    """把引擎输出 metadata 规范化到固定字段集合。"""
    output = default_metadata()
    if isinstance(raw_metadata, dict):
        for key in output.keys():
            if key in raw_metadata:
                output[key] = raw_metadata[key]

    if not isinstance(output.get("events"), list):
        output["events"] = []

    return output


@asynccontextmanager
async def lifespan(_: FastAPI):
    """FastAPI 生命周期：启动时初始化引擎，关闭时清理缓存。"""
    global ENGINE
    ENGINE = InferenceEngine()
    yield
    ENGINE = None
    with session_storage_lock:
        session_storage.clear()


app = FastAPI(title="ASR Chunk Service", version="1.0.0", lifespan=lifespan)

# 跨域准入：联调阶段允许所有来源。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    """服务健康检查。"""
    status = {
        "model_loaded": False,
        "device": "unknown",
        "model_name": "iic/SenseVoiceSmall",
    }
    if ENGINE is not None:
        status = ENGINE.get_status()

    return {
        "ok": True,
        "status": "running",
        "device": status.get("device", "unknown"),
        "model_loaded": bool(status.get("model_loaded", False)),
        "model_name": status.get("model_name", "iic/SenseVoiceSmall"),
    }


@app.post("/asr/chunk")
async def asr_chunk(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    chunk_index: int = Form(...),
    is_final: bool = Form(False),
    language: str = Form("zh"),
    use_itn: bool = Form(True),
):
    """
    接收一个切片并识别当前会话的“完整累计音频”。

    流程：
    1) 读取当前切片 bytes；
    2) 追加到 session_storage[session_id]；
    3) 把累计 bytes 写临时文件给 engine.transcribe_file；
    4) is_final=True 时清理该 session 的缓存。
    """
    temp_file_path: Optional[Path] = None
    source_name = file.filename or "chunk.wav"

    try:
        if ENGINE is None:
            raise RuntimeError("InferenceEngine 未初始化")

        # 读取当前切片。
        content = await file.read()
        if not content:
            raise ValueError("收到空切片，无法识别")

        # 追加到会话缓存，并复制当前完整音频。
        with session_storage_lock:
            if session_id not in session_storage:
                session_storage[session_id] = bytearray()
            session_storage[session_id].extend(content)
            full_audio_bytes = bytes(session_storage[session_id])

        # 写完整累计音频到临时文件。
        suffix = Path(source_name).suffix or ".wav"
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
            prefix=f"asr_{session_id}_{chunk_index}_",
        ) as temp_file:
            temp_file.write(full_audio_bytes)
            temp_file_path = Path(temp_file.name)

        # 调用共享引擎识别。
        result = ENGINE.transcribe_file(
            audio_path=str(temp_file_path),
            language=language,
            use_itn=use_itn,
        )

        response = {
            "ok": bool(result.get("ok", False)),
            "session_id": session_id,
            "chunk_index": chunk_index,
            "is_final": is_final,
            "text": result.get("text", ""),
            "raw_text": result.get("raw_text", ""),
            "metadata": normalize_metadata(result.get("metadata")),
            "language": result.get("language", language),
            "device": result.get("device", "unknown"),
            "elapsed_ms": result.get("elapsed_ms", 0.0),
            "filename": source_name,
        }

        if not response["ok"]:
            response["error"] = result.get("error", "推理失败")
            return JSONResponse(status_code=500, content=response)

        return response

    except Exception as error:
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "session_id": session_id,
                "chunk_index": chunk_index,
                "is_final": is_final,
                "text": "",
                "raw_text": "",
                "metadata": default_metadata(),
                "language": language,
                "device": "unknown" if ENGINE is None else ENGINE.device,
                "elapsed_ms": 0.0,
                "filename": source_name,
                "error": str(error),
            },
        )

    finally:
        # 清理临时文件。
        try:
            if temp_file_path is not None and temp_file_path.exists():
                os.remove(temp_file_path)
        except Exception:
            traceback.print_exc()

        # 最后一片处理完后，释放会话缓存。
        if is_final:
            try:
                with session_storage_lock:
                    if session_id in session_storage:
                        del session_storage[session_id]
            except Exception:
                traceback.print_exc()

        # 关闭上传文件句柄。
        try:
            await file.close()
        except Exception:
            traceback.print_exc()


def main():
    """支持 python .\\service\\app.py 启动。"""
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=18080)


if __name__ == "__main__":
    main()
