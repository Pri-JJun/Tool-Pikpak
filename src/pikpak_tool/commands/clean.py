"""CLEAN 기능 (빈 폴더 완전 삭제)"""

from __future__ import annotations

from pikpak_tool.rclone import run_rclone
from pikpak_tool.utils import normalize_remote


def run_clean(remote: str, dry_run: bool) -> None:
    """원격 전체를 검사하여 빈 폴더를 완전 삭제 (하위→상위 연쇄, 루트는 보존)"""
    remote = normalize_remote(remote)
    print(f"[clean] '{remote}:' 빈 폴더 검사 중...{' (DRY-RUN)' if dry_run else ''}")

    # rmdirs: 비어 있는 디렉터리를 하위→상위 순으로 모두 제거
    #   --leave-root       : 원격 루트 자체는 삭제하지 않음
    #   --pikpak-use-trash : false → 완전 삭제(휴지통 미경유)
    args = [
        "rmdirs",
        f"{remote}:",
        "--leave-root",
        "--pikpak-use-trash=false",
    ]
    if dry_run:
        # 삭제 예정 폴더를 rclone 로그로 미리 표시 (실제 삭제 없음)
        args += ["--dry-run", "-v"]

    run_rclone(args, capture=False)
    print("[clean] 완료" + (" (dry-run: 실제 삭제 없음)" if dry_run else ""))
