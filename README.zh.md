# FocusLens — AI 专注力追踪

基于摄像头的桌面应用，实时检测分心行为并追踪专注度。基于 **PyQt6**、**OpenCV** 和 **MediaPipe** 构建。

## 致谢

本项目基于 [Ayotomide Ogunsami](https://www.linkedin.com/in/ayotomide-ogunsami-93aa61312) 的原始 **FocusCam** 进行全面重构与增强。原始项目的创意——通过摄像头实时检测分心——由她提出，此版本在 PyQt6 图形界面、多线程架构、专注历史持久化以及大量交互优化方面进行了大幅扩展。

感谢所有在开发过程中提供反馈和建议的人。

## 功能特点

- **实时面部与眼部追踪** — 基于 MediaPipe FaceMesh 的分心程度评分（0–100%）
- **专注度进度条** — 颜色编码进度条（绿 → 黄 → 红）
- **专注时序图** — 60 秒迷你折线图，展示专注度波动
- **专注历史网格** — 6 周贡献图，月份以边框色相区分
- **分心记录** — 自动记录每次分心事件及时间戳和持续时间
- **可折叠面板** — 每个区块均可点击标题折叠/展开
- **登录系统** — MySQL 数据库用户认证
- **摄像头设置** — 可调节阈值、灵敏度及提醒偏好
- **声音提醒** — 检测到分心时发出声音反馈

## 技术栈

| 组件 | 技术 |
|-----------|-----------|
| 图形界面 | PyQt6 |
| 面部检测 | MediaPipe FaceMesh |
| 计算机视觉 | OpenCV |
| 数据库(本地) | SQLite |
| 数据库(用户) | MySQL |
| 音频 | QSound / winsound |
| 打包 | PyInstaller |

## 安装

```bash
# 克隆仓库
git clone https://github.com/pycant/FocusLens.git
cd FocusLens

# 安装依赖
pip install -r requirements.txt

# 运行应用
python main.py
```

### 环境要求

- Python 3.10+（MediaPipe 兼容性要求）
- 摄像头
- MySQL 服务器（可选，用户登录功能）

## 使用方法

1. 运行 `python main.py` 启动应用
2. 登录或注册新账号
3. 摄像头将自动启动
4. 右侧面板实时显示专注统计数据
5. 点击区块标题（▼）可折叠/展开任意面板

### 操作说明

| 按键/操作 | 功能 |
|-----------|----------|
| **开始/停止** | 切换摄像头检测 |
| **设置** | 调整检测阈值、提醒方式 |
| **视图 → 侧边面板** | 显示/隐藏统计面板 |
| **折叠 ▲** | 点击区块标题隐藏内容 |

## 项目结构

```
FocusLens/
├── app/                    # 图形界面模块
│   ├── main_window.py      # 主窗口（摄像头视图）
│   ├── camera_widget.py    # 摄像头画面 + 检测工作线程
│   ├── statistics_widget.py# 统计面板
│   ├── contribution_grid.py# 专注历史网格
│   ├── distraction_overlay.py # 分心提醒浮层
│   ├── login_dialog.py     # 用户登录/注册
│   ├── settings_dialog.py  # 设置界面
│   └── theme.py            # 主题管理
├── core/                   # 核心逻辑
│   ├── detector.py         # 面部/眼部检测
│   ├── distraction_engine.py # 分心状态机
│   └── camera_manager.py   # 摄像头管理
├── config/                 # 配置文件
├── utils/                  # 工具函数
├── resources/              # 图标、音效、模型
└── main.py                 # 入口文件
```

## 开源协议

本项目基于 MIT 协议开源。
