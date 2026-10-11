# 发布到自己的 GitHub

本目录已按独立源码仓库整理。上传前确认根目录含 README.md、LICENSE、NOTICE.md、源码、翻译和测试；`build/`、`backup/`、旧版 `backups/`、应用包、二进制、ZIP 和个人数据被 `.gitignore` 排除。

建议仓库名称 `NeatDownloadManager-zh`，简介：`macOS Neat Download Manager 1.3.24 简体中文补丁与 Command-W 窗口快捷键`。

在 GitHub 创建自己的空仓库，不预建 README 或 License，然后在本目录执行以下命令。替换占位符为自己的仓库地址：

```sh
git init -b main
git add .
git status --short
git diff --cached --stat
git commit -m "Add NDM 1.3.24 Chinese patch and Command-W support"
git remote add origin https://github.com/YOUR_USERNAME/NeatDownloadManager-zh.git
git push -u origin main
```

提交前应检查 `git status`，不要使用 `git add -f` 加入构建结果或备份。MIT 许可仅覆盖本项目补丁源码；本仓库不授予对 NDM 应用本体的再分发权。首次发布建议使用源码仓库及 GitHub 自动生成的源码压缩包，用户自行提供原版应用构建。

可按 CHANGELOG.md 创建 v1.0.3 Release，说明仅支持指定 1.3.24 指纹、macOS 11+、两种架构，以及需原版备份。此整理步骤未创建远程仓库、提交或推送任何内容。
