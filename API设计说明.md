# API设计说明

## 1. 文档目的

本文档用于前后端联调阶段，描述当前 ASR 服务的接口草稿、请求字段、返回字段、会话协议和错误码标准。

当前项目中已实现的接口：

- `GET /health`
- `POST /asr/chunk`

当前项目中尚未实现、但建议补充的接口：

- `POST /asr/file`

## 2. 基本约定

### 2.1 服务说明

- 服务框架：FastAPI
- 当前服务名称：`ASR Chunk Service`
- 当前默认模型：`iic/SenseVoiceSmall`
- 当前默认语言：`zh`
- 当前默认 ITN：`true`

### 2.2 Content-Type 约定

- `GET /health`：无请求体
- `POST /asr/file`：建议使用 `multipart/form-data`
- `POST /asr/chunk`：当前实现使用 `multipart/form-data`

### 2.3 统一返回格式

为便于前端联调，本文档统一采用以下响应包裹结构作为协议标准。

成功：

```json
{
  "ok": true,
  "code": "OK",
  "message": "success",
  "data": {}
}
```

失败：

```json
{
  "ok": false,
  "code": "EMPTY_CHUNK",
  "message": "收到空切片，无法识别",
  "data": null
}
```

字段说明：

| 字段名 | 类型 | 是否必返 | 含义 |
| --- | --- | --- | --- |
| `ok` | `boolean` | 是 | 是否成功 |
| `code` | `string` | 是 | 机器可读状态码；成功固定为 `OK`，失败为错误码 |
| `message` | `string` | 是 | 人类可读提示信息 |
| `data` | `object \| null` | 是 | 成功时为业务数据对象，失败时为 `null` |

### 2.4 当前实现与协议草稿的关系

- 当前代码中的 `/health` 和 `/asr/chunk` 还没有完全按本文档的统一外层结构返回。
- 本文档面向“前端联调协议收口”，即以后续联调和改造目标为准。
- 其中 `/asr/file` 为建议设计草稿，当前代码尚未实现。

## 3. 数据结构说明

### 3.1 metadata 结构

识别接口中的 `metadata` 字段建议按以下固定结构返回：

| 字段名 | 类型 | 是否必返 | 含义 |
| --- | --- | --- | --- |
| `language` | `string \| null` | 是 | 从模型原始标签中解析出的语言标签，如 `zh`、`en` |
| `emotion` | `string \| null` | 是 | 从标签中解析出的情绪，如 `HAPPY`、`SAD` |
| `events` | `string[]` | 是 | 从标签中解析出的事件列表，如 `Speech`、`BGM`、`Laughter` |
| `has_speech` | `boolean` | 是 | 是否包含 `Speech` 事件 |
| `itn_mode` | `string \| null` | 是 | 标签中的 ITN 模式，如 `withitn`、`woitn` |
| `unknown_tags` | `string[]` | 是 | 未识别的标签原文 |

默认空结构示例：

```json
{
  "language": null,
  "emotion": null,
  "events": [],
  "has_speech": false,
  "itn_mode": null,
  "unknown_tags": []
}
```

### 3.2 ASRResult 结构

`POST /asr/file` 和 `POST /asr/chunk` 成功时，`data` 建议统一为以下结构：

| 字段名 | 类型 | 是否必返 | 含义 |
| --- | --- | --- | --- |
| `session_id` | `string` | 条件必返 | 分片场景下返回；文件直传场景可不返回 |
| `chunk_index` | `integer` | 条件必返 | 分片场景下返回；文件直传场景可不返回 |
| `is_final` | `boolean` | 条件必返 | 分片场景下返回；文件直传场景可不返回 |
| `text` | `string` | 是 | 清洗后的识别文本，已去除标签、emoji 和多余空白 |
| `raw_text` | `string` | 是 | 模型原始文本，可能包含标签 |
| `metadata` | `object` | 是 | 标签解析结果，结构见 `metadata` 说明 |
| `language` | `string` | 是 | 本次识别使用的语言参数 |
| `device` | `string` | 是 | 推理设备 |
| `elapsed_ms` | `number` | 是 | 本次推理耗时，单位毫秒 |
| `filename` | `string` | 是 | 上传文件名 |

## 4. GET /health

### 4.1 接口用途

用于服务存活检查和模型加载状态检查。

### 4.2 请求信息

- Method：`GET`
- Path：`/health`
- Content-Type：无

### 4.3 请求字段

无请求字段。

### 4.4 成功返回

```json
{
  "ok": true,
  "code": "OK",
  "message": "success",
  "data": {
    "status": "running",
    "device": "cpu",
    "model_loaded": true,
    "model_name": "iic/SenseVoiceSmall"
  }
}
```

### 4.5 `data` 字段说明

| 字段名 | 类型 | 是否必返 | 含义 |
| --- | --- | --- | --- |
| `status` | `string` | 是 | 服务状态，当前固定为 `running` |
| `device` | `string` | 是 | 模型运行设备 |
| `model_loaded` | `boolean` | 是 | 模型是否已成功加载 |
| `model_name` | `string` | 是 | 当前模型名称 |

### 4.6 联调说明

- 当 `data.model_loaded=false` 时，说明服务进程可访问，但识别接口可能不可用。
- 建议前端在进入识别页面前先调用一次该接口。

## 5. POST /asr/file

### 5.1 接口状态

该接口当前项目中尚未实现，以下为基于当前代码能力整理的建议设计草稿。

### 5.2 接口用途

用于一次性上传完整音频文件并返回单次识别结果，适合非分片上传场景。

### 5.3 请求信息

- Method：`POST`
- Path：`/asr/file`
- Content-Type：`multipart/form-data`

### 5.4 请求字段

| 字段名 | 类型 | 是否必填 | 含义 |
| --- | --- | --- | --- |
| `file` | `file` | 是 | 完整音频文件 |
| `language` | `string` | 否 | 识别语言，默认建议为 `zh` |
| `use_itn` | `boolean` | 否 | 是否开启 ITN，默认建议为 `true` |

### 5.5 成功返回

```json
{
  "ok": true,
  "code": "OK",
  "message": "success",
  "data": {
    "text": "今天天气很好。",
    "raw_text": "<|zh|><|Speech|>今天天气很好。",
    "metadata": {
      "language": "zh",
      "emotion": null,
      "events": ["Speech"],
      "has_speech": true,
      "itn_mode": null,
      "unknown_tags": []
    },
    "language": "zh",
    "device": "cpu",
    "elapsed_ms": 1350.216,
    "filename": "demo.wav"
  }
}
```

### 5.6 `data` 字段说明

| 字段名 | 类型 | 是否必返 | 含义 |
| --- | --- | --- | --- |
| `text` | `string` | 是 | 清洗后的识别文本 |
| `raw_text` | `string` | 是 | 模型原始文本，可能包含标签 |
| `metadata` | `object` | 是 | 标签解析结果，结构见 `metadata` 说明 |
| `language` | `string` | 是 | 本次识别使用的语言参数 |
| `device` | `string` | 是 | 推理设备 |
| `elapsed_ms` | `number` | 是 | 识别耗时，单位毫秒 |
| `filename` | `string` | 是 | 上传文件名 |

### 5.7 失败返回

```json
{
  "ok": false,
  "code": "EMPTY_FILE",
  "message": "上传文件为空",
  "data": null
}
```

### 5.8 联调说明

- 该接口建议和 `/asr/chunk` 保持同一套返回结构，便于前端复用展示逻辑。
- 如果后端后续决定暴露时间戳能力，可增加 `timestamp` 字段，但建议作为可选扩展字段。

## 6. POST /asr/chunk

### 6.1 接口用途

用于分片上传音频，并基于同一 `session_id` 将所有已上传切片进行累计识别。

### 6.2 特别说明

`/asr/chunk` 当前返回的是“当前会话下累计全量音频”的识别结果，不是“本次 chunk 的增量文本”。

也就是说：

- 第 1 片返回第 1 片累计文本
- 第 2 片返回第 1 + 第 2 片累计文本
- 第 3 片返回第 1 + 第 2 + 第 3 片累计文本

前端如果希望展示增量字幕，需要自行与上次结果对比，或者后端未来提供真正的增量接口。

### 6.3 请求信息

- Method：`POST`
- Path：`/asr/chunk`
- Content-Type：`multipart/form-data`

### 6.4 请求字段

| 字段名 | 类型 | 是否必填 | 含义 |
| --- | --- | --- | --- |
| `file` | `file` | 条件必填 | 当前上传的音频切片 |
| `session_id` | `string` | 是 | 会话唯一标识，用于关联多个 chunk |
| `chunk_index` | `integer` | 是 | 当前切片序号 |
| `is_final` | `boolean` | 否 | 是否为最后一个切片，默认 `false` |
| `language` | `string` | 否 | 识别语言，默认 `zh` |
| `use_itn` | `boolean` | 否 | 是否开启 ITN，默认 `true` |

### 6.5 分片协议

#### `session_id`

- 同一段音频的所有 chunk 必须使用同一个 `session_id`
- 不同会话必须使用不同 `session_id`
- 当前服务端会在内存中按 `session_id` 缓存累计音频

#### `chunk_index`

- 当前代码中主要用于回传展示和临时文件命名
- 当前服务端未对顺序、连续性、重复提交做严格校验
- 建议前端从 `0` 或 `1` 开始单调递增，并避免乱序发送

#### `is_final`

- 当值为 `true` 时，表示当前请求是该会话的结束请求
- 当前服务端会在本次请求结束后清理当前 `session_id` 对应的缓存
- 前端应在最后一次请求时显式传入 `true`

#### 空 chunk 与 finalize 协议

这一条为联调必执行标准，必须写死：

- `is_final=false` 且 `file` 为空：报错，返回 `EMPTY_CHUNK`
- `is_final=true` 且 `file` 为空：允许，表示只结束会话，不触发识别

说明：

- 该规则用于兼容录音停止时前端可能发送空 Blob 作为结束信号的场景
- 如果是“带音频数据的最后一片”，则应传 `is_final=true` 且 `file` 非空，此时正常识别并在响应后清理缓存
- 如果是“纯结束信号”，则传 `is_final=true` 且 `file` 为空，此时只清理会话，不做识别，返回成功确认

### 6.6 成功返回

#### 场景 A：普通分片或带音频的最后一片

```json
{
  "ok": true,
  "code": "OK",
  "message": "success",
  "data": {
    "session_id": "session_001",
    "chunk_index": 2,
    "is_final": false,
    "text": "今天天气很好。",
    "raw_text": "<|zh|><|Speech|>今天天气很好。",
    "metadata": {
      "language": "zh",
      "emotion": null,
      "events": ["Speech"],
      "has_speech": true,
      "itn_mode": null,
      "unknown_tags": []
    },
    "language": "zh",
    "device": "cpu",
    "elapsed_ms": 963.541,
    "filename": "chunk_0002.wav"
  }
}
```

#### 场景 B：空 chunk finalize，仅结束会话

```json
{
  "ok": true,
  "code": "OK",
  "message": "session finalized",
  "data": {
    "session_id": "session_001",
    "chunk_index": 3,
    "is_final": true,
    "finalized_only": true
  }
}
```

### 6.7 `data` 字段说明

#### 场景 A：识别成功

| 字段名 | 类型 | 是否必返 | 含义 |
| --- | --- | --- | --- |
| `session_id` | `string` | 是 | 当前会话 ID |
| `chunk_index` | `integer` | 是 | 当前请求的切片序号 |
| `is_final` | `boolean` | 是 | 当前切片是否为最后一片 |
| `text` | `string` | 是 | 当前累计全量音频对应的清洗后文本 |
| `raw_text` | `string` | 是 | 当前累计全量音频对应的模型原始文本 |
| `metadata` | `object` | 是 | 标签解析结果，结构见 `metadata` 说明 |
| `language` | `string` | 是 | 本次识别使用的语言参数 |
| `device` | `string` | 是 | 推理设备 |
| `elapsed_ms` | `number` | 是 | 本次识别耗时，单位毫秒 |
| `filename` | `string` | 是 | 当前上传切片的原始文件名 |

#### 场景 B：空 chunk finalize 成功

| 字段名 | 类型 | 是否必返 | 含义 |
| --- | --- | --- | --- |
| `session_id` | `string` | 是 | 当前会话 ID |
| `chunk_index` | `integer` | 是 | 当前请求的切片序号 |
| `is_final` | `boolean` | 是 | 固定为 `true` |
| `finalized_only` | `boolean` | 是 | 固定为 `true`，表示本次仅结束会话，未执行识别 |

### 6.8 失败返回

```json
{
  "ok": false,
  "code": "EMPTY_CHUNK",
  "message": "收到空切片，无法识别",
  "data": null
}
```

### 6.9 联调注意事项

- 当前后端是把同一 `session_id` 下的音频字节直接累计后重新识别，不是模型级别的流式增量推理。
- 当前后端未保证 chunk 乱序时的结果正确性，前端应尽量串行、按序发送。
- 当前后端仅在 `is_final=true` 后清理会话缓存，如果前端未发送结束请求，缓存会继续保留在服务内存中。

## 7. 错误码标准

### 7.1 当前实现现状

当前项目中：

- `/health` 正常返回 `200`
- `/asr/chunk` 在模型未初始化、空文件、推理失败等情况下，当前实现基本统一返回 `500`

### 7.2 V1 必须支持的错误码

联调阶段先固定以下 6 个错误码，作为 V1 最小可执行标准：

| 错误码 | HTTP 状态码建议 | 适用接口 | 含义 |
| --- | --- | --- | --- |
| `MODEL_NOT_READY` | `503` | `/asr/file` `/asr/chunk` | 模型未加载成功或推理引擎不可用 |
| `EMPTY_FILE` | `400` | `/asr/file` | 上传文件为空 |
| `EMPTY_CHUNK` | `400` | `/asr/chunk` | 分片为空，且本次请求不是合法的 finalize-only 请求 |
| `INVALID_SESSION` | `409` | `/asr/chunk` | 会话不存在、已关闭，或会话状态冲突 |
| `UNSUPPORTED_AUDIO_FORMAT` | `415` | `/asr/file` `/asr/chunk` | 文件格式或媒体类型不支持 |
| `ASR_INFERENCE_FAILED` | `500` | `/asr/file` `/asr/chunk` | ASR 推理过程中出现内部异常 |

### 7.3 推荐错误返回格式

```json
{
  "ok": false,
  "code": "MODEL_NOT_READY",
  "message": "模型未加载完成，暂时无法识别",
  "data": null
}
```

### 7.4 非 V1 的可扩展错误码

以下错误码可以后续按需补充，不作为当前联调阻塞项：

- `INVALID_ARGUMENT`
- `FILE_TOO_LARGE`
- `SESSION_ALREADY_FINALIZED`
- `INTERNAL_ERROR`

## 8. 前端联调建议

### 8.1 `/health`

- 页面初始化时先调用一次，判断模型是否可用

### 8.2 `/asr/file`

- 适合一次性上传完整录音文件
- 适合离线识别、单文件识别页面

### 8.3 `/asr/chunk`

- 适合边录音边上传的场景
- 前端应维护 `session_id`
- 前端应保证 chunk 尽量按顺序发送
- 前端应明确区分“带音频的最后一片”和“空 chunk finalize”
- 前端应在结束时一定发送一次 `is_final=true`
- 前端展示时应明确区分“累计全量文本”和“增量文本”

## 9. 版本说明

本草稿基于当前项目代码整理，其中：

- `GET /health`：已实现
- `POST /asr/chunk`：已实现，但当前返回结构与本文档统一外层协议仍有差异
- `POST /asr/file`：尚未实现，为建议设计草稿

