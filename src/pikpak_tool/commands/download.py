"""DOWNLOAD 기능"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import PurePosixPath

from pikpak_tool.rclone import run_rclone
from pikpak_tool.utils import (
    OUTPUT_DIR,
    load_paths_from_file,
    normalize_remote,
    reset_output_dir,
)


def run_download(
    remote: str,
    folder: str,
    transfers: int,
    dry_run: bool,
    files_from: str | None = None,
) -> None:
    remote = normalize_remote(remote)

    # 입력 방식 상호 배타 검증: -f(폴더)와 --from(목록) 동시 지정 불가
    base = folder.strip().strip("/")
    if files_from and base:
        sys.exit("[ERROR] -f/--folder 와 --from 은 함께 사용할 수 없습니다.")

    # --- --from 모드: 목록 파일의 경로를 --files-from 으로 다운로드 ---
    if files_from:
        targets = load_paths_from_file(files_from)
        if not targets:
            print("[INFO] 대상 파일이 없습니다. (목록 파일이 비어 있음)")
            return

        # 목록을 임시 파일로 정규화(빈 줄 제거본)하여 --files-from 에 전달
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                "w", suffix=".txt", delete=False, encoding="utf-8"
            ) as f:
                f.write("\n".join(targets) + "\n")
                tmp_path = f.name

            if not dry_run:
                reset_output_dir()  # dry-run 시에는 기존 결과물 보존

            # 경로 전체 구조를 ./output 아래에 그대로 재현
            args = [
                "copy",
                f"{remote}:",
                OUTPUT_DIR,
                "--files-from",
                tmp_path,
                "--transfers",
                str(transfers),
                "-P",
            ]
            if dry_run:
                args.append("--dry-run")

            print(
                f"[download] 목록 '{files_from}'의 {len(targets)}개 파일  ->  {OUTPUT_DIR}"
                f"  (transfers={transfers}{', DRY-RUN' if dry_run else ''})"
            )
            run_rclone(args, capture=False)  # 진행률 실시간 출력
            print("[download] 완료" + (" (dry-run: 실제 전송 없음)" if dry_run else ""))
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
        return

    # --- 폴더 모드: 지정 폴더(또는 루트)를 다운로드 (기존 동작) ---
    src = f"{remote}:{base}" if base else f"{remote}:"

    # 로컬 저장 위치: ./output 아래에 원격 최상위 폴더명 유지
    top = PurePosixPath(base).name if base else ""

    if not dry_run:
        reset_output_dir()  # dry-run 시에는 기존 결과물 보존
    dest = f"{OUTPUT_DIR}/{top}" if top else OUTPUT_DIR

    args = ["copy", src, dest, "--transfers", str(transfers), "-P"]
    if dry_run:
        args.append("--dry-run")

    print(f"[download] {src}  ->  {dest}  (transfers={transfers}{', DRY-RUN' if dry_run else ''})")
    run_rclone(args, capture=False)  # 진행률 실시간 출력
    print("[download] 완료" + (" (dry-run: 실제 전송 없음)" if dry_run else ""))
