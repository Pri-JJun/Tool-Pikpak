"""공통 유틸"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

# 다운로드/스캔 결과가 저장되는 고정 로컬 폴더
OUTPUT_DIR = "./output"


def normalize_remote(remote: str) -> str:
    """'pikpak' / 'pikpak:' 어느 쪽으로 입력해도 콜론 없는 이름으로 통일"""
    return remote.rstrip(":")


def reset_output_dir() -> Path:
    """로컬 ./output 폴더가 존재하면 삭제 후 재생성"""
    out = Path(OUTPUT_DIR)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    return out


def normalize_ext(ext: str) -> str:
    """'.ASC' / 'ASC' / 'asc' -> 'asc' (점 제거 + 소문자)"""
    return ext.strip().lstrip(".").lower()


def load_paths_from_file(files_from: str) -> list[str]:
    """--from 파일에서 경로 목록을 읽어 반환 (빈 줄 제거)"""
    p = Path(files_from).expanduser()
    if not p.is_file():
        sys.exit(f"[ERROR] 목록 파일을 찾을 수 없습니다: {files_from}")
    lines = p.read_text(encoding="utf-8").splitlines()
    return [ln.strip() for ln in lines if ln.strip()]
