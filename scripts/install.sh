#!/usr/bin/env bash
set -euo pipefail

APP="printlabelms"
REPO="gusya1/PrintLabelMS"
API_BASE="https://api.github.com/repos/${REPO}/releases"
DOWNLOAD_BASE="https://github.com/${REPO}/releases/download"

data_dir="${XDG_DATA_HOME:-$HOME/.local/share}/${APP}"
config_dir="${XDG_CONFIG_HOME:-$HOME/.config}/${APP}"
bin_dir="$HOME/.local/bin"
cache_dir="${XDG_CACHE_HOME:-$HOME/.cache}/${APP}"
versions_dir="${data_dir}/versions"
current_link="${data_dir}/current"
previous_link="${data_dir}/previous"
icon_path="${data_dir}/icon.png"
desktop_file="${XDG_DATA_HOME:-$HOME/.local/share}/applications/${APP}.desktop"

usage() {
    cat <<EOF
PrintLabelMS installer (без sudo, установка в домашний каталог)

Usage: bash install.sh [опции]

Опции:
  --version X.Y.Z   установить конкретную версию (по умолчанию — последний релиз)
  --force           переустановить даже при уже установленной версии
  -h, --help        этот текст
EOF
}

die() {
    echo "Ошибка: $*" >&2
    exit 1
}

target_version=""
force=0
while [[ $# -gt 0 ]]; do
    case "$1" in
        --version)
            [[ $# -ge 2 ]] || die "--version требует значение X.Y.Z"
            target_version="$2"
            shift 2
            ;;
        --force)
            force=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            die "Неизвестный аргумент: $1 (см. --help)"
            ;;
    esac
done

if [[ -n "$target_version" ]] && ! [[ "$target_version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    die "Некорректная версия: ${target_version} (ожидается X.Y.Z)"
fi

# --- preflight
command -v python3 >/dev/null 2>&1 || die "python3 не найден. Установите Python 3.12+ (например: sudo apt install python3)."
if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)'; then
    py_version="$(python3 -c 'import sys; print("{}.{}".format(sys.version_info.major, sys.version_info.minor))')"
    die "Найден Python ${py_version}, требуется 3.12+."
fi
command -v git >/dev/null 2>&1 || die "git не найден — нужен для установки moy_sklad из GitHub (sudo apt install git)."
command -v curl >/dev/null 2>&1 || die "curl не найден (sudo apt install curl)."

# --- уже установлена?
if [[ -L "$current_link" ]] && [[ $force -eq 0 ]]; then
    echo "PrintLabelMS уже установлен. Делегирую обновление: current/venv/bin/${APP} update"
    exec "$(readlink -f "$current_link")/venv/bin/${APP}" update
fi

# --- релиз
if [[ -n "$target_version" ]]; then
    tag="v${target_version}"
    api_url="${API_BASE}/tags/${tag}"
else
    api_url="${API_BASE}/latest"
fi
info="$(curl -fsSL "$api_url")" || die "Не удалось получить информацию о релизе (${api_url}). Проверьте сеть и наличие релиза."
tag_name="$(printf '%s' "$info" | python3 -c 'import json, sys; print(json.load(sys.stdin)["tag_name"])')"
version="${tag_name#v}"
wheel_name="${APP}-${version}-py3-none-any.whl"

# --- скачивание и проверка
mkdir -p "$cache_dir"
curl -fsSL "${DOWNLOAD_BASE}/${tag_name}/${wheel_name}" -o "${cache_dir}/${wheel_name}" \
    || die "Не удалось скачать ${wheel_name}."
curl -fsSL "${DOWNLOAD_BASE}/${tag_name}/SHA256SUMS" -o "${cache_dir}/SHA256SUMS" \
    || die "Не удалось скачать SHA256SUMS."
expected="$(awk -v f="$wheel_name" '$2 == f {print $1}' "${cache_dir}/SHA256SUMS")"
[[ -n "$expected" ]] || die "Контрольная сумма ${wheel_name} не найдена в SHA256SUMS."
actual="$(sha256sum "${cache_dir}/${wheel_name}" | awk '{print $1}')"
[[ "$actual" == "${expected,,}" ]] || die "SHA256 не совпадает для ${wheel_name}: ожидалось ${expected}, получено ${actual}."

# --- установка в каталог версии
mkdir -p "$versions_dir"
tmp_dir="${versions_dir}/${version}.tmp-$$"
cleanup() {
    if [[ -n "${tmp_dir:-}" && -d "$tmp_dir" ]]; then
        rm -rf "$tmp_dir"
    fi
}
trap cleanup EXIT
rm -rf "$tmp_dir"
mkdir -p "$tmp_dir"
python3 -m venv "${tmp_dir}/venv" || die "Не удалось создать venv. На Debian/Ubuntu: sudo apt install python3-venv."
"${tmp_dir}/venv/bin/pip" install --upgrade "${cache_dir}/${wheel_name}" \
    || die "pip install провален (нужны git и сеть для moy_sklad)."
"${tmp_dir}/venv/bin/${APP}" --version >/dev/null \
    || die "Health-check провален: ${APP} --version."
QT_QPA_PLATFORM=offscreen "${tmp_dir}/venv/bin/python" -c 'import gui.ui.mainwindow_ui' \
    || die "Health-check провален: импорт GUI (gui/ui отсутствует в wheel?)."

target_dir="${versions_dir}/${version}"
if [[ -L "$current_link" ]]; then
    old_target="$(readlink -f "$current_link")"
    ln -sfn "$old_target" "$previous_link"
fi
rm -rf "$target_dir"
mv "$tmp_dir" "$target_dir"
tmp_dir=""
trap - EXIT
rm -f "$current_link"
ln -s "$target_dir" "$current_link"

# --- ротация: храним две версии
ls -1 "$versions_dir" | grep -E '^[0-9]+(\.[0-9]+)+$' | sort -V | head -n -2 \
    | while read -r old; do rm -rf "${versions_dir}/${old}"; done

# --- конфиг (не перезаписываем существующий)
mkdir -p "$config_dir"
if [[ ! -f "${config_dir}/settings.json" ]]; then
    cat > "${config_dir}/settings.json" <<'EOF'
{
  "schema_version": 1,
  "moy_sklad_token": "ВСТАВЬТЕ_ТОКЕН_МОЙСКЛАДА",
  "check_updates": true,
  "printer": {
    "name": "ИМЯ_ПРИНТЕРА",
    "resolution": 600
  },
  "label_formats": [
    {
      "width": 58,
      "height": 40,
      "width_offset": 0,
      "height_offset": 0,
      "orientation": "Portrait"
    },
    {
      "width": 74,
      "height": 120,
      "width_offset": 0,
      "height_offset": 0,
      "orientation": "Landscape"
    }
  ]
}
EOF
fi

# --- launcher
mkdir -p "$bin_dir"
ln -sfn "${data_dir}/current/venv/bin/${APP}" "${bin_dir}/${APP}"

# --- PATH
case ":${PATH}:" in
    *":${bin_dir}:"*) ;;
    *)
        if ! grep -qs "printlabelms-path" "${HOME}/.bashrc"; then
            printf '\n# printlabelms-path\nexport PATH="%s:$PATH"\n' "$bin_dir" >> "${HOME}/.bashrc"
        fi
        echo "~/.local/bin добавлен в PATH (~/.bashrc); для текущего терминала: source ~/.bashrc."
        ;;
esac

# --- иконка
icon_src="$("${target_dir}/venv/bin/python" -c 'from resources import get_resource_path; print(get_resource_path("pictures/icon.png"))')"
cp "$icon_src" "$icon_path"

# --- .desktop (меню + рабочий стол)
write_desktop() {
    local dest="$1"
    mkdir -p "$(dirname "$dest")"
    cat > "$dest" <<EOF
[Desktop Entry]
Type=Application
Name=PrintLabelMS
Comment=Печать этикеток из МойСклада
Exec=${bin_dir}/${APP}
Icon=${icon_path}
Terminal=false
Categories=Utility;
EOF
    chmod +x "$dest"
}
write_desktop "$desktop_file"
desktop_target="$(xdg-user-dir DESKTOP 2>/dev/null || true)"
[[ -n "$desktop_target" ]] || desktop_target="${HOME}/Desktop"
write_desktop "${desktop_target}/${APP}.desktop"
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$(dirname "$desktop_file")"
fi

echo "PrintLabelMS ${version} установлен."
echo "Запуск: ${APP} (или ${bin_dir}/${APP}); ярлык на рабочем столе: ${desktop_target}/${APP}.desktop"
echo "Конфиг: ${config_dir}/settings.json — вставьте токен МойСклада перед первым запуском."
