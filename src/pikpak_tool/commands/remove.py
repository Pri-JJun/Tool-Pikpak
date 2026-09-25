"""DELETE / PURGE 기능 (지정 확장자 파일 제거)"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

from pikpak_tool.rclone import run_rclone, run_rclone_stream
from pikpak_tool.utils import load_paths_from_file, normalize_ext, normalize_remote


def list_matching(remote: str, extensions: list[str]) -> list[str]:
    """확장자를 소문자로 변환해 비교하여 매칭되는 파일 경로 목록 반환"""
    targets = {normalize_ext(e) for e in extensions}
    matched: list[str] = []

    for path in run_rclone_stream(["lsf", "--recursive", "--files-only", f"{remote}:"]):
        suffix = Path(path).suffix.lstrip(".").lower()  # 소문자 변환 후 비교
        if suffix and suffix in targets:
            matched.append(path)

    return matched


def delete_files(remote: str, paths: list[str], permanent: bool) -> None:
    """--files-from 으로 매칭 파일을 일괄 삭제. permanent=True 면 휴지통 미경유(완전 삭제)"""
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("\n".join(paths) + "\n")
            tmp_path = f.name

        args = ["delete", f"{remote}:", "--files-from", tmp_path]
        # PikPak 삭제 정책: use-trash=true(휴지통 이동) / false(완전 삭제)
        args.append(f"--pikpak-use-trash={'false' if permanent else 'true'}")
        run_rclone(args, capture=False)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


def run_removal(
    remote: str,
    extensions: list[str],
    permanent: bool,
    dry_run: bool,
    files_from: str | None = None,
) -> None:
    remote = normalize_remote(remote)
    mode = "완전 삭제" if permanent else "휴지통 이동"

    # 입력 방식 상호 배타 검증: extensions 와 --from 은 동시에/모두 없이 올 수 없음
    if files_from and extensions:
        sys.exit("[ERROR] 확장자 인자와 --from 은 함께 사용할 수 없습니다.")
    if not files_from and not extensions:
        sys.exit("[ERROR] 확장자 인자 또는 --from 중 하나는 반드시 지정해야 합니다.")

    # --- --from 모드: 파일 목록을 그대로 삭제 대상으로 사용 (dry-run 미지원) ---
    if files_from:
        if dry_run:
            print(
                "[WARN] --from 모드에서는 --dry-run 이 적용되지 않습니다. 실제 삭제를 진행합니다."
            )
        targets = load_paths_from_file(files_from)
        if not targets:
            print("[INFO] 대상 파일이 없습니다. (목록 파일이 비어 있음)")
            return
        print(f"[{mode}] 목록 파일 '{files_from}'에서 {len(targets)}개 경로 로드")
        print(f"[INFO] {mode} 실행 중...")
        delete_files(remote, targets, permanent=permanent)
        print(f"[DONE] {len(targets)}개 파일 {mode} 완료")
        return

    # --- 확장자 모드: 원격을 스캔해 매칭 파일 삭제 (dry-run 지원) ---
    exts = [normalize_ext(e) for e in extensions]
    print(f"[{mode}] '{remote}:'에서 확장자 {exts} 파일 검색 중...")

    targets = list_matching(remote, exts)
    if not targets:
        print("[INFO] 대상 파일이 없습니다.")
        return

    print(f"[INFO] 대상 {len(targets)}개 파일 발견:")
    preview = targets[:20]
    for p in preview:
        print(f"   - {p}")
    if len(targets) > len(preview):
        print(f"   ... 외 {len(targets) - len(preview)}개")

    if dry_run:
        print(f"[DRY-RUN] 실제 {mode}는 수행하지 않았습니다.")
        return

    print(f"[INFO] {mode} 실행 중...")
    delete_files(remote, targets, permanent=permanent)
    print(f"[DONE] {len(targets)}개 파일 {mode} 완료")
