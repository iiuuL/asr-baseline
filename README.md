# asr-baseline


本项目是在 **SenseVoice / FunASR** 开源能力基础上开展的工程化整理工作，面向中文自动语音识别（ASR）任务的项目仓库。该项目围绕“**音频输入 -> 文本输出**”的基础链路展开，目标是提供一个可复用、可调用、可扩展的中文语音识别基线工程，支持本地推理、HTTP 服务调用。



#### 我的主要工作

本项目主要围绕中文 ASR 基线的工程化落地开展整理与实现，具体包括：

- 基于 SenseVoice / FunASR 搭建中文语音识别基线
- 封装核心推理逻辑，支持本地调用与服务复用
- 搭建 FastAPI 服务接口，支持 HTTP 调用
- 支持音频分片上传与会话式识别流程
- 对项目仓库、文档与运行流程进行整理，支持后续继续扩展与集成
  


#### 项目简介

在给定音频输入的条件下，模型输出对应的中文识别文本，并支持服务化调用与结构化结果返回。仓库内已经整理了核心推理模块、服务层代码、示例页面、接口文档与辅助说明。

核心输出通常围绕以下字段展开：

```text
{
  "text": "...",
  "raw_text": "...",
  "metadata": {...},
  "elapsed_ms": ...
}
```

其中：

* `text`：清洗后的识别文本
* `raw_text`：原始识别输出
* `metadata`：语言、情绪、声学事件等补充信息
* `elapsed_ms`：推理耗时等统计信息

如需最简评测输出，也可仅返回：

```text
{"result": "这是一个测试语音。"}
```



#### 仓库结构

```text
asr-baseline/
├── asr_core/                       # 核心推理与识别逻辑
├── service/                        # FastAPI 服务层
├── docs/                           # 项目文档
│   ├── api.md
│   ├── api-design-draft.md
│   └── project-structure-notes.md
├── examples/                       # 示例页面与示例资源
│   ├── web_demo/
│   │   └── demo.html
│   └── eval_demo/
│       └── demo1.html
├── scripts/
│   └── windows/
│       └── run_service.cmd
├── environment.yml
├── requirements.txt
├── CHANGELOG.md
└── LICENSE
```

核心目录说明：

```text
asr-baseline/
├── asr_core/                       # 模型加载、推理调用、结果处理
├── service/                        # HTTP 接口、会话管理、配置相关
├── docs/api.md                     # API 接入说明
├── examples/web_demo/demo.html     # 本地联调示例页面
└── scripts/windows/run_service.cmd # Windows 启动脚本
```

#### 环境要求

推荐环境：

* Python `3.10`
* PyTorch `2.x`
* Windows 10/11 或 Linux
* 如需 GPU 推理，建议使用 NVIDIA GPU + CUDA 环境

安装依赖：

```bash
pip install -r requirements.txt
```

或使用 Conda 环境文件：

```bash
conda env create -f environment.yml
conda activate asr-baseline
```

如果需要 GPU 版 PyTorch，可按实际 CUDA 版本单独安装，例如：

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
```

#### 快速开始

#### 1. 克隆仓库

```bash
git clone https://github.com/iiuuL/asr-baseline.git
cd asr-baseline
```

#### 2. 安装依赖

```bash
pip install -r requirements.txt
```

或：

```bash
conda env create -f environment.yml
conda activate asr-baseline
```

#### 3. 启动服务

Windows 下可直接使用脚本：

```bat
scripts\windows\run_service.cmd
```

或手动启动服务：

```bash
python -m service.app
```

#### 4. 健康检查

服务启动后，可先检查：

```text
GET /health
```

#### 5. 打开示例页面联调

可使用：

```text
examples/web_demo/demo.html
```

该页面可用于本地录音、分片上传与接口联调验证。

#### API 概览

本项目当前提供的核心接口包括：

* `GET /health`

  * 用于服务健康检查

* `POST /asr/chunk`

  * 用于上传音频分片并获取识别结果

其中，`/asr/chunk` 支持分片上传场景，可用于实现录音过程中的逐段识别与会话收尾。
当最后一个有效分片上传完成时，可通过 `is_final=true` 触发最终收尾处理。

更详细的字段说明、请求方式和调用约定见：

```text
docs/api.md
```

#### 服务输出说明

项目支持返回结构化识别结果，便于后续系统集成。常见返回内容包括：

* `text`：清洗后的识别文本
* `raw_text`：原始识别输出
* `metadata.language`：识别语言
* `metadata.emotion`：情绪标签
* `metadata.events`：声学事件标签
* `elapsed_ms`：处理耗时

如仅用于评测接口，也可采用更简化的输出格式，以满足固定评测要求。

#### 示例

仓库中提供了简单的前端示例页面，可用于本地联调与接口验证：

* Web 示例：`examples/web_demo/demo.html`
* 评测相关示例：`examples/eval_demo/demo1.html`

这些示例主要用于演示调用流程，不代表完整产品形态。

#### 文档

* API 接入说明：`docs/api.md`
* API 设计草稿：`docs/api-design-draft.md`
* 项目结构说明：`docs/project-structure-notes.md`
* 更新记录：`CHANGELOG.md`



#### 当前定位与说明

这是一个面向工程接入和原型验证的 ASR 基线仓库，重点在于：

* 将语音识别能力整理为清晰的服务接口
* 支持本地快速部署与联调
* 为上层系统集成提供稳定起点

它并不以“生产级语音平台”为目标，因此当前仓库默认不包含完整的部署编排、监控体系、CI/CD 或复杂测试基础设施。

#### 后续可扩展方向

- 补充详细的接口示例与错误处理说明
- 增加规范的服务启动入口与配置管理
- 增加文本后处理、热词、说话风格标签或会话级逻辑
- 面向具体任务场景继续优化模型识别效果与推理表现


### 致谢

本项目实现过程中参考或复用了以下工作：

* `SenseVoice`
* `FunASR`
* FastAPI 服务化封装思路
* 中文语音识别工程接入与评测需求
