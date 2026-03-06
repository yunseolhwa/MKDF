#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -f "fishing_master.py" ]]; then
  echo "[ERROR] fishing_master.py 파일이 없습니다. 게임 코드를 루트에 추가해 주세요."
  exit 1
fi

rm -rf build/web
mkdir -p build

python -m pygbag --build --ume_block 0 --out build/web fishing_master.py

echo "[OK] 웹 빌드 완료: build/web"
