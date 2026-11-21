#!/usr/bin/env bash
# Установка poppler для Linux (poppler-utils + poppler-data).
set -euo pipefail

if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y poppler-utils poppler-data
elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y poppler-utils
else
    echo "Пакетный менеджер не найден (apt-get/dnf). Установите poppler-utils вручную." >&2
    exit 1
fi

echo "poppler установлен: $(pdfinfo --version | head -n 1)"
echo "В settings.json задайте poppler_path = null или /usr/bin"
