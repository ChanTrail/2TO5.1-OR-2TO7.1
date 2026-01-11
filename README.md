# 🎵 立体声转5.1&7.1声道混音工具

<p align="center">
  <strong>Web GUI 版本 v3.0.0</strong><br>
  <em>将普通立体声音频转换为沉浸式环绕声体验</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-3.0.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/python-3.12-green.svg" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-orange.svg" alt="License">
  <img src="https://img.shields.io/badge/platform-Windows-lightgrey.svg" alt="Platform">
</p>

---

## 📖 简介

立体声转5.1&7.1声道混音工具是一款专业级音频转换应用，可将普通立体声（2.0）音频智能转换为家庭影院级别的 **5.1** 或 **7.1** 环绕声格式。

本工具采用先进的 **BS-RoFormer** 深度学习模型进行音频源分离，将原始音频分解为人声、低音、鼓声、吉他、钢琴、伴奏等独立音轨，然后通过可视化 Web GUI 界面让用户自由调整各声道的混音配置，最终输出高质量的多声道环绕声音频。

**开发者**: ChanTrail

## ✨ 功能特点

### 🎛️ Web GUI 可视化界面
- 现代化的 Web 界面，直观易用
- 实时预览混音效果
- 可视化环绕声声道布局
- 支持独奏/静音单个声道

### 🔊 智能音频处理
- **双模式转换**：支持 5.1 和 7.1 环绕声格式，可随时切换
- **智能音频分离**：将音频分离为 7 个独立音轨（vocals, bass, drums, guitar, piano, instrumental, other）
- **自定义声道配置**：自由调整每个声道的音源和音量
- **配置槽功能**：保存和快速切换多组混音配置

### 📦 批量处理
- 支持多文件批量处理
- 一键应用配置到所有文件
- 智能跳过已处理文件
- 实时显示分离进度

### 🚀 高性能
- **GPU 加速**：支持 CUDA 加速（推荐 3GB+ 显存）
- **CPU 模式**：无显卡也可使用
- **高质量输出**：FLAC 无损格式

## 💻 系统要求

| 项目 | 最低要求 | 推荐配置 |
|------|---------|---------|
| 操作系统 | Windows 10 | Windows 10/11 |
| Python | 3.12（整合包已内置） | 3.12 |
| 显卡 | - | NVIDIA GPU (≥3GB 显存) |
| 内存 | 8GB | 16GB+ |
| 磁盘空间 | 10GB | 20GB+ |

## 📥 安装说明

### 整合包用户（推荐）

本程序提供整合包形式，已包含所有依赖项和 Python 环境，**无需额外安装**。

下载并解压整合包
[下载](https://github.com/CHEN-Technology/2TO5.1-OR-2TO7.1/releases/latest)


### 手动安装

```bash
# 克隆仓库
git clone https://github.com/CHEN-Technology/2TO5.1-OR-2TO7.1.git
cd 2TO5.1-OR-2TO7.1

# 安装依赖
pip install -r requirements.txt

# 下载模型文件到 logic_bsroformer/models/
```
`logic_roformer.pt`
- [HuggingFace 下载](https://huggingface.co/ChenTechnology/logic_bsroformer/resolve/main/logic_roformer.pt)
## 🚀 快速开始

### 方式一：双击启动
```
双击 start.bat
```

### 方式二：命令行启动
```bash
.\Python\python main.py
```

### 使用流程

1. **启动程序** → 自动打开浏览器访问 Web GUI
2. **选择配置**：
   - 处理模式：GPU（推荐）或 CPU
   - 声道模式：5.1 或 7.1
   - 输入/输出目录
3. **开始处理** → 等待音频分离完成
4. **调整混音**：
   - 在混音器界面调整各声道配置
   - 实时预览混音效果
   - 保存常用配置到配置槽
5. **导出文件** → 获得高质量环绕声音频

## 📁 目录结构

```
2TO5.1-OR-2TO7.1/           
├── main.py                 # 主程序入口
├── web_mixer.py            # Web GUI 服务器
├── web_templates/          # Web 页面模板
│   ├── setup.html          # 设置页面
│   └── mixer.html          # 混音器页面
├── logic_bsroformer/       # 音频分离模块
│   ├── inference.py        # 推理脚本
│   ├── configs/            # 模型配置
│   └── models/             # 模型文件 (需下载)
├── temp/                   # 临时文件目录 (分离时自动生成)
├── Python/                 # 内置 Python 环境
├── tests/                  # 测试用例
├── requirements.txt        # 依赖列表
├── envinstall.bat          # Python 软件包安装脚本
├── start.bat               # 启动脚本
├── README.md               # 说明文档
└── LICENSE                 # 许可证

```

## 🎚️ 声道配置

### 5.1 声道布局
| 声道 | 英文名 | 默认音源 |
|------|--------|---------|
| 左前 (L) | Left Front | drums (左声道) |
| 右前 (R) | Right Front | drums (右声道) |
| 中置 (C) | Center | vocals (单声道) |
| 低音 (LFE) | Low Frequency Effects | bass (单声道) |
| 左环绕 (LS) | Left Surround | instrumental, other, vocals |
| 右环绕 (RS) | Right Surround | instrumental, other, vocals |

### 7.1 声道布局
在 5.1 基础上增加：
| 声道 | 英文名 | 默认音源 |
|------|--------|---------|
| 左后环绕 (LB) | Left Back | guitar, other, instrumental, vocals |
| 右后环绕 (RB) | Right Back | guitar, other, instrumental, vocals |

## 🔧 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                    Web GUI (Flask)                       │
├─────────────────────────────────────────────────────────┤
│  setup.html          │           mixer.html              │
│  - 参数配置          │           - 声道混音配置          │
│  - 目录选择          │           - 实时预览              │
│  - 处理进度显示      │           - 配置槽管理            │
└─────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│                 Audio Processing Engine                  │
├─────────────────────────────────────────────────────────┤
│  BS-RoFormer Model     │    PyDub + NumPy + SoundFile   │
│  - 音频源分离          │    - 声道混音                   │
│  - GPU/CPU 加速        │    - FLAC 编码                  │
└─────────────────────────────────────────────────────────┘
```

## ❓ 常见问题

<details>
<summary><strong>Q: GPU 模式运行出错？</strong></summary>

确保：
1. 已安装 NVIDIA 显卡驱动
2. 显存 ≥ 3GB
3. 如仍有问题，切换到 CPU 模式

</details>

<details>
<summary><strong>Q: 处理速度很慢？</strong></summary>

- 推荐使用 GPU 模式
- 长音频文件需要更多处理时间
- CPU 模式下处理速度较慢是正常现象

</details>

<details>
<summary><strong>Q: 为什么输出是 FLAC 格式？</strong></summary>

FLAC 是无损压缩格式，可以：
- 保持原始音频质量
- 支持多声道音频
- 文件大小适中

</details>

<details>
<summary><strong>Q: 如何保留分离的临时文件？</strong></summary>

程序退出时会询问是否删除临时文件，选择"取消"即可保留。

</details>

## 📋 依赖项

### 核心依赖
- **Flask** - Web 服务器
- **PyDub** - 音频处理
- **NumPy** - 数值计算
- **SoundFile** - 音频文件 I/O

### 深度学习
- **PyTorch 2.8.0+cu129** - 深度学习框架
- **TorchAudio** - 音频处理
- **BS-RoFormer** - 音频分离模型

### 其他
- librosa, tqdm, einops, omegaconf 等

完整依赖列表请参见 `requirements.txt`

## 📄 许可证

本项目采用 GPL-3.0 许可证。详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- [BS-RoFormer](https://github.com/lucidrains/BS-RoFormer) - 音频分离模型
- [PyDub](https://github.com/jiaaro/pydub) - 音频处理库
- [Flask](https://flask.palletsprojects.com/) - Web 框架

---

<p align="center">
  <strong>立体声转5.1&7.1声道混音工具 v3.0.0</strong><br>
  <em>by ChanTrail</em>
</p>
