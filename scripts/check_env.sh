#!/usr/bin/env bash
set -euo pipefail

# Probe interpreters for required libs: gi/Gtk4, cryptography, argon2
# Checks: active python, /usr/bin/python3, conda run -n passvault python

check_py() {
  local label="$1"; shift
  local cmd=("$@")
  local ok="FAIL"
  if "${cmd[@]}" - <<'PY' >/dev/null 2>&1; then ok="PASS"; fi
  printf "%-24s %s\n" "$label" "$ok"
  return 0
PY
import gi, cryptography, argon2
gi.require_version('Gtk','4.0')
from gi.repository import Gtk
print('OK')
PY
}

echo "DISPLAY=${DISPLAY:-unset} WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-unset} XDG_SESSION_TYPE=${XDG_SESSION_TYPE:-unset}"
printf "%-24s %s\n" "Interpreter" "Deps"
printf "%-24s %s\n" "------------------------" "----"

if command -v python >/dev/null 2>&1; then
  check_py "python (active)" "$(command -v python)"
else
  printf "%-24s %s\n" "python (active)" "N/A"
fi

if [ -x "/usr/bin/python3" ]; then
  check_py "/usr/bin/python3" "/usr/bin/python3"
else
  printf "%-24s %s\n" "/usr/bin/python3" "N/A"
fi

if command -v conda >/dev/null 2>&1; then
  check_py "conda run -n passvault" conda run -n passvault --no-capture-output python
else
  printf "%-24s %s\n" "conda run -n passvault" "N/A"
fi

echo
echo "PASS means interpreter has gi/Gtk4, cryptography, argon2."
echo "If all are FAIL, install deps:"
echo "- Arch (system): sudo pacman -S --needed python-gobject gtk4 python-cryptography python-argon2-cffi"
echo "- Conda: conda install -c conda-forge pygobject pycairo gobject-introspection gtk4 cryptography argon2-cffi"
