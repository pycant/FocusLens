# FocusLens — AI 专注力追踪

> [English](README.md) | [**中文版**](README.zh.md)

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
| 数据库（专注日志） | SQLite |
| 数据库（用户账户） | MySQL |
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

## 数据库说明

FocusLens 使用两套数据库系统分别存储不同类型的数据：

### SQLite — 专注日志（本地自动存储）

每日专注分钟数自动存储在 `focus_stats.db` 中。该数据库在应用启动时自动创建，无需手动配置。

```
focus_log 表结构：
  username TEXT  — 用户名
  date     TEXT  — 日期（YYYY-MM-DD 格式）
  minutes  REAL  — 该日专注总分钟数
```

专注历史网格的数据即来源于此数据库，展示近 6 周的专注贡献图。

### MySQL — 用户账户（可选）

用户注册和登录功能需要 MySQL 服务器支持。数据库建表脚本位于 `resources/focuslens.sql`。

```sql
-- users 表（应用启动时自动创建）
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**配置步骤：**

1. 安装 MySQL 服务器并创建数据库（例如 `focuslens_db`）
2. 修改 `utils/database.py` 中的 MySQL 连接信息
3. 启动应用——数据表会自动创建

如果未配置 MySQL，应用仍可正常运行，但用户认证功能不可用。

## 从源码打包

你可以将 FocusLens 打包为独立的 Windows 可执行文件：

```bash
# 需要 conda 环境包含所有依赖
conda run -n yolo_env python scripts/build.py quick     # 仅打包 exe
conda run -n yolo_env python scripts/build.py all        # 完整打包（exe + 更新程序）
```

| 脚本 | 用途 |
|--------|---------|
| `scripts/build.py` | 构建自动化（exe、更新程序、安装程序） |
| `scripts/FocusLens.spec` | PyInstaller 配置文件 |
| `scripts/updater.py` | 独立更新程序（检查 GitHub Releases） |
| `scripts/installer/FocusLens.iss` | Inno Setup 安装程序脚本 |

**输出：**
- `dist/FocusLens/FocusLens.exe` — 打包应用（无需 Python 环境）
- `dist/FocusLensUpdater.exe` — 独立更新程序（7.9 MB）

> 打包后的应用约 140 MB（包含 MediaPipe 和 OpenCV 依赖）。如需制作安装程序，请安装 [Inno Setup 6](https://jrsoftware.org/isdl.php) 后运行 `python scripts/build.py installer`。

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
├── utils/                  # 工具函数（数据库、日志）
├── resources/              # 图标、音效、模型、SQL 建表脚本
├── main.py                 # 入口文件
├── README.md               # 英文文档
├── README.zh.md            # 中文文档
└── LICENSE                 # MIT 协议
```

## 开源协议

本项目基于 [MIT 协议](LICENSE) 开源。
