#!/usr/bin/env bash
set -euo pipefail

PRESET_NAME="${1:?Preset name (e.g., Linux/X11)}"
GODOT_PROJECT_DIR="${2:-godot}"
EXPORT_PATH="${3:-build/linux/scrabbot.x86_64}"

# Préparer le workspace
WORKDIR="$(pwd)"

# Installer Godot localement si absent
GODOT_BIN="godot"
if ! command -v godot >/dev/null 2>&1; then
  echo "Godot non trouvé dans le PATH, installation locale dans .tools..."
  TOOLS_DIR="${WORKDIR}/.tools/godot"
  mkdir -p "${TOOLS_DIR}"
  GODOT_VERSION_FULL_DEFAULT="4.4-stable"
  GODOT_VERSION_FULL="${GODOT_VERSION_FULL:-${GODOT_VERSION_FULL_DEFAULT}}"
  EDITOR_URL="https://github.com/godotengine/godot/releases/download/${GODOT_VERSION_FULL}/Godot_v${GODOT_VERSION_FULL}_linux.x86_64.zip"
  TMP_ZIP="${TOOLS_DIR}/godot.zip"
  if ! command -v curl >/dev/null 2>&1; then
    echo "Erreur: curl est requis pour installer Godot." >&2
    exit 1
  fi
  if ! command -v unzip >/dev/null 2>&1; then
    echo "Erreur: unzip est requis pour installer Godot." >&2
    exit 1
  fi
  echo "Téléchargement Godot: ${EDITOR_URL}"
  curl -L -o "${TMP_ZIP}" "${EDITOR_URL}"
  rm -rf "${TOOLS_DIR}/editor"
  mkdir -p "${TOOLS_DIR}/editor"
  unzip -q -o "${TMP_ZIP}" -d "${TOOLS_DIR}/editor"
  FOUND_BIN=$(ls -1 "${TOOLS_DIR}/editor"/Godot_v*_linux.x86_64 2>/dev/null | head -n1 || true)
  if [ -z "${FOUND_BIN}" ]; then
    echo "Erreur: binaire Godot introuvable après extraction." >&2
    exit 1
  fi
  mv "${FOUND_BIN}" "${TOOLS_DIR}/godot"
  chmod +x "${TOOLS_DIR}/godot"
  GODOT_BIN="${TOOLS_DIR}/godot"
else
  GODOT_BIN="$(command -v godot)"
fi

# Crée le dossier d'export relatif au projet Godot
# Prépare les répertoires d'export et de cache dans le workspace (pas dans /home)

# Si le chemin fourni n'est pas absolu, construire un chemin ABSOLU basé sur le workspace
ABS_EXPORT_PATH="${EXPORT_PATH}"
if [ "${EXPORT_PATH#\/}" = "${EXPORT_PATH}" ]; then
  ABS_EXPORT_PATH="${WORKDIR}/${GODOT_PROJECT_DIR}/${EXPORT_PATH}"
fi

mkdir -p "$(dirname "${ABS_EXPORT_PATH}")"

# Dossiers HOME/XDG_CACHE_HOME isolés et accessibles en écriture
WORKSPACE_HOME_DIR="${WORKDIR}/.home"
WORKSPACE_CACHE_DIR="${WORKDIR}/.cache"
mkdir -p "${WORKSPACE_CACHE_DIR}/godot" "${WORKSPACE_HOME_DIR}"

############################################################
# Préparer les templates d'export Godot si absents
############################################################

# Utiliser les dossiers HOME/XDG_CACHE_HOME dans le workspace
export HOME="${WORKSPACE_HOME_DIR}"
export XDG_CACHE_HOME="${WORKSPACE_CACHE_DIR}"

# Récupérer la version de Godot (ex: "Godot Engine v4.4.stable.official.xxxxx")
GODOT_VERSION_RAW="$(godot --headless --version || godot --version || true)"
# Exemple: 4.4.stable.official.4c311cbee
GODOT_VERSION_NUM="$(echo "${GODOT_VERSION_RAW}" | cut -d'.' -f1-2)"
GODOT_VERSION_STABLE="$(echo "${GODOT_VERSION_RAW}" | cut -d'.' -f1-2)".stable

TEMPLATES_BASE_DIR="${HOME}/.local/share/godot/export_templates"
TEMPLATES_DIR="${TEMPLATES_BASE_DIR}/${GODOT_VERSION_STABLE}"

REQUIRED_TEMPLATES=(
  "linux_debug.x86_64"
  "linux_release.x86_64"
)

ensure_templates() {
  local missing=0
  for f in "${REQUIRED_TEMPLATES[@]}"; do
    if [ ! -f "${TEMPLATES_DIR}/${f}" ]; then
      missing=1
      break
    fi
  done
  if [ "${missing}" -eq 0 ]; then
    return 0
  fi

  echo "Templates d'export Godot absents pour ${GODOT_VERSION_STABLE}, téléchargement..."
  mkdir -p "${TEMPLATES_BASE_DIR}"

  # Exemple URL: https://github.com/godotengine/godot/releases/download/4.4-stable/Godot_v4.4-stable_export_templates.tpz
  local tag="${GODOT_VERSION_NUM}-stable"
  local filename="Godot_v${GODOT_VERSION_NUM}-stable_export_templates.tpz"
  local url="https://github.com/godotengine/godot/releases/download/${tag}/${filename}"

  local tpz_path="${WORKSPACE_CACHE_DIR}/${filename}"
  if ! command -v curl >/dev/null 2>&1; then
    echo "Erreur: curl est requis pour télécharger les templates." >&2
    exit 1
  fi
  echo "Téléchargement: ${url}"
  curl -L -o "${tpz_path}" "${url}"

  if ! command -v unzip >/dev/null 2>&1; then
    echo "Erreur: unzip est requis pour extraire les templates." >&2
    exit 1
  fi
  local tmp_dir="${WORKSPACE_CACHE_DIR}/godot_templates_unpack"
  rm -rf "${tmp_dir}"
  mkdir -p "${tmp_dir}"
  unzip -q -o "${tpz_path}" -d "${tmp_dir}"
  if [ ! -d "${tmp_dir}/templates" ]; then
    echo "Erreur: archive de templates inattendue (dossier 'templates' introuvable)." >&2
    exit 1
  fi
  rm -rf "${TEMPLATES_DIR}"
  mv "${tmp_dir}/templates" "${TEMPLATES_DIR}"
  rm -rf "${tmp_dir}"

  echo "Templates installés dans: ${TEMPLATES_DIR}"
}

ensure_templates

echo "Export Godot preset='${PRESET_NAME}' vers '${ABS_EXPORT_PATH}' (projet: ${GODOT_PROJECT_DIR})"

godot --headless \
  --path "${GODOT_PROJECT_DIR}" \
  --export-release "${PRESET_NAME}" "${ABS_EXPORT_PATH}"

echo "Export terminé: ${ABS_EXPORT_PATH}"
