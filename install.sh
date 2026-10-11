#!/bin/bash
# One-command entry point; paths are resolved relative to this script.
set -euo pipefail
PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if ! command -v python3 >/dev/null 2>&1; then
    echo '安装失败：未找到 Python 3。请先安装 Xcode Command Line Tools：xcode-select --install' >&2
    exit 1
fi
exec python3 "$PROJECT_DIR/quick_install.py" "$@"
