# Neat Download Manager 1.3.24 中文补丁（macOS）

针对 **Neat Download Manager 1.3 / Build 24** 的简体中文补丁源码，支持 Apple Silicon 与 Intel，并新增 **⌘W 关闭当前窗口**。当前补丁版本 **1.0.3**，已在实际应用中安装测试。

参考 [hardwin2023/NeatDownloadManager-zh](https://github.com/hardwin2023/NeatDownloadManager-zh) 的汉化思路，针对 1.3.24 重新处理 NIB 与主程序。保留原图标、事件连接和窗口布局，修复设置/关于等按钮汉化后无反应的问题，并在显示层翻译侧边栏全部分类及“已完成 / 未完成”。

本仓库提供补丁源码、翻译表和构建工具。**需要自行提供未经修改的原版应用**；仓库不包含 NDM 应用本体、原始 NIB、图标或下载数据。

## 功能

- 汉化 18 个 NIB 文件中的 378 处显示引用，包括主界面、设置、关于、下载和属性等窗口。
- 同步处理依赖英文标题分发的菜单/工具栏命令，保持按钮行为。
- 在侧边栏最终显示位置翻译全部 8 项名称，保留内部分类、状态值和图标名称。
- 保留主程序原始 ASCII 字符串区，避免新建视频下载及浏览器接管时抛出异常。
- 保留官方 Safari 扩展的文件、签名及沙盒权限；仅签名修改后的主应用和新增动态库。
- ⌘W 关闭普通可关闭窗口；有附属弹窗时优先取消/关闭弹窗。主窗口沿用原关闭按钮的行为，关闭窗口不会执行“完全退出”。
- 快捷键只在 NDM 进程内处理；不会改变其他应用的快捷键。按住 ⌘W 不会连续关闭多个窗口。

## 支持范围与要求

- 仅支持原版 **1.3 (Build 24)** 的特定 universal 二进制，简称 1.3.24；构建前严格校验版本、主程序 SHA-256 和全部 NIB 指纹。
- 本完整版本要求 **macOS 11 或更新版本**，含 arm64 和 x86_64。
- Python 3.9+、Xcode Command Line Tools 或完整 Xcode（`clang`、`lipo`、`codesign`、`ditto`）。无需 pip 依赖。
- Apple Silicon 同时执行 Intel 原生测试需要 Rosetta。Intel 可以编译两种架构，但仅能运行 x86_64 测试。

## 快速安装

### 方式一：自动安装脚本（推荐）

1. 下载本项目源码 ZIP 并解压，或克隆自己的 GitHub 仓库；在终端进入项目文件夹。
2. 打开官方 **NeatDMInstaller.dmg**，把里面未经修改的 **NeatDownloadManager.app** 完整复制到本项目的 **`original/`** 文件夹。官方应用也应已安装在 `/Applications`。
3. 等待下载完成，在 NDM 中点击“完全退出”，然后运行：

```sh
./install.sh
```

原版文件应放在这里：

```text
NeatDownloadManager-zh/
├── install.sh
└── original/
    └── NeatDownloadManager.app
```

不需要手动运行构建或签名命令。脚本自动完成：

- 检查指定文件夹是否有官方原版，缺少时提示复制位置。
- 校验原版版本、文件指纹和签名；拒绝已汉化或不兼容的应用。
- 检查 NDM 是否已安装、是否完全退出及编译工具是否可用。
- 构建中文界面、侧边栏和 Command-W 模块。
- 保留官方 Safari 扩展签名和权限，对修改后的主应用与模块本地签名并验证。
- 备份当前完整应用，安装修复版；安装校验失败时恢复原应用。

安装完成后手动启动 `/Applications/NeatDownloadManager.app` 即可。原版、构建结果和备份不会提交到 GitHub，下载任务及分片不会被改动。

如果提示缺少编译工具，请先运行 `xcode-select --install`，完成安装后重新运行脚本。需要 Python 3.9+ 和 macOS 11+。

### 方式二：只生成 App，再手动安装

同样先将官方原版放入 `original/`，然后运行：

```sh
./install.sh --build-only
```

脚本打印生成的 App 路径。完全退出 NDM 后，先备份旧 App，再用 Finder 将生成的完整 App 替换到“应用程序”。

## 备份与恢复

自动安装在**项目根目录**新建 `backup/`，把旧应用完整备份到 `backup/NeatDownloadManager.backup-时间戳.app`，对应 JSON 恢复记录也保存在这里。不会在“应用程序”目录留下备份 App。无论从哪个终端目录调用脚本，备份位置都以脚本所在项目为准。请保留需要的完整备份及记录。

```sh
python3 install.py restore --record "backup/NeatDownloadManager.backup-时间戳.json"
```

恢复前也要完全退出 NDM。恢复当前应用时，同样先将它备份到项目 `backup/`。确认新版本工作正常后，可把不再需要的旧 App 备份移到废纸篓。旧版 `backups/` 下的 JSON 记录仍可以指定路径恢复。

## 高级用法

默认安装到 `/Applications/NeatDownloadManager.app`；其他安装位置可指定：

```sh
./install.sh --target "/path/to/NeatDownloadManager.app"
```

脚本需要对目标所在目录有写权限，不自动提权。若无法替换，可使用 `--build-only`，然后通过 Finder 安装。

单独指定构建输入、输出仍然可用：

```sh
python3 build.py --source "/path/to/original/NeatDownloadManager.app" --output "build/manual/NeatDownloadManager.app"
python3 install.py install --app "build/manual/NeatDownloadManager.app"
```

输出目录已存在时请换一个路径，不要使用 `python3 -O`。自动脚本每次使用新的构建目录，因此可直接重复运行。

## 验证

```sh
python3 tests/run.py
```

测试无需原应用，涵盖共享图标字符串保护、版本拒绝、加载命令空间检查、安装失败回滚，以及两种架构实际执行的侧边栏汇编和 AppKit 快捷键处理。详情见 [验证记录](docs/VERIFICATION.md)。

1.0.1 已实测新建长链接的下载/取消、Chrome 自动接管下载、Safari 右键“Download by NeatDownloadManager”送出下载，以及设置/关于/下载完成窗口的 ⌘W。Safari 普通点击下载是否自动接管取决于官方扩展自身能力，本项目未新增该功能。

如持有原版应用，可额外执行真实二进制回归检查（内部分类对象和整个 ASCII 字符串区必须保持原值）：

```sh
NDM_ORIGINAL_APP="/path/to/original/NeatDownloadManager.app" python3 tests/run.py
```

## 目录

| 路径 | 内容 |
| --- | --- |
| `install.sh` / `quick_install.py` | 检查原版、一键构建及安装 |
| `original/` | 用户放入官方原版应用的位置 |
| `build.py` | 原版校验、完整构建、签名 |
| `install.py` | 整包安装、备份、恢复 |
| `ndm_patch/` | NIB 汉化、Mach-O 解析、常量补丁、侧边栏/动态库加载补丁 |
| `src/NDMWindowShortcuts.m` | ⌘W 的 Objective-C 源码 |
| `src/asm/` | arm64 与 x86_64 侧边栏显示包装代码 |
| `data/translations.json` | 中文翻译映射 |
| `data/compatibility.json` | 支持的原版文件指纹 |
| `tests/` | Python 结构/安装测试和原生测试 |
| `docs/` | 实现说明、验证、发布步骤 |

## 已知限制

补丁只处理已识别的界面文字，部分运行时错误信息等可能仍显示英文。没有改变原布局，个别长文案受原控件宽度限制。NDM 更新后请不要直接使用旧补丁；新版本需要重新分析和适配。重新签名属于本地签名，不等于 Apple 公证。

## 相关说明

实现细节见 [TECHNICAL.md](docs/TECHNICAL.md)，验证记录见 [VERIFICATION.md](docs/VERIFICATION.md)。

## 许可证

本项目仅提供汉化补丁及相关工具，不包含 Neat Download Manager 本身。Neat Download Manager 的版权归其原作者 **Javad Motallebi** 所有。

汉化补丁代码采用 [MIT 许可证](LICENSE) 发布，可在保留许可证及版权声明的前提下自由使用、修改和分发。应用本体的版权与授权不受本补丁许可证影响，来源及版权说明详见 [NOTICE.md](NOTICE.md)。

## 致谢

- [Neat Download Manager](https://www.neatdownloadmanager.com/) — 感谢 **Javad Motallebi** 开发这款免费、实用的下载管理器。
- [hardwin2023/NeatDownloadManager-zh](https://github.com/hardwin2023/NeatDownloadManager-zh) — 感谢 **[hardwin2023](https://github.com/hardwin2023)** 分享 macOS 汉化方法及翻译内容，为本项目适配 1.3.24 提供参考。
- 感谢所有为本项目提供建议、测试和反馈的用户。
