"""RENAME 기능"""

from __future__ import annotations

import sys
from pathlib import PurePosixPath

from pikpak_tool.rclone import run_rclone
from pikpak_tool.utils import normalize_remote


def list_paths(remote: str, base: str, dirs: bool) -> list[str]:
    """base 하위 상대경로 목록. dirs=False→파일만, True→폴더만."""
    flag = "--dirs-only" if dirs else "--files-only"
    out = run_rclone(["lsf", "-R", flag, "--format", "p", f"{remote}:{base}"])
    return [line.rstrip("/") for line in out.splitlines() if line.strip()]


def plan_renames(rel_paths: list[str], remove: str) -> list[tuple[str, str]]:
    """(old_rel, new_rel) 목록. 이름(basename)에서만 문자열 제거."""
    plans: list[tuple[str, str]] = []
    for rel in rel_paths:
        p = PurePosixPath(rel)
        old_name = p.name
        if remove not in old_name:
            continue
        new_name = old_name.replace(remove, "")
        if not new_name or new_name == old_name:
            continue
        plans.append((rel, str(p.with_name(new_name))))
    return plans


def apply_renames(
    remote: str, base: str, plans: list[tuple[str, str]], dry_run: bool
) -> tuple[int, int]:
    base = base.rstrip("/")
    changed = skipped = 0
    for old_rel, new_rel in plans:
        old_full = f"{remote}:{base}/{old_rel}" if base else f"{remote}:{old_rel}"
        new_full = f"{remote}:{base}/{new_rel}" if base else f"{remote}:{new_rel}"
        if dry_run:
            print(f"[DRY] {old_rel}  ->  {new_rel}")
            continue
        try:
            run_rclone(["moveto", old_full, new_full])
            changed += 1
            print(f"[OK ] {old_rel}  ->  {new_rel}")
        except SystemExit as e:
            skipped += 1
            print(f"[FAIL] {old_rel} ({e})", file=sys.stderr)
    return changed, skipped


def run_rename(remote: str, folder: str, remove: str, include_folders: bool, dry_run: bool) -> None:
    remote = normalize_remote(remote)
    base = folder.strip().strip("/")

    # 1) 파일
    files = list_paths(remote, base, dirs=False)
    file_plans = plan_renames(files, remove)
    print(f"[파일] 대상 {len(files)}개 중 변경 대상 {len(file_plans)}개")
    c1, s1 = apply_renames(remote, base, file_plans, dry_run)

    # 2) 폴더(옵션) — 깊은 경로부터 처리해 상위 변경으로 하위 경로가 깨지지 않게
    c2 = s2 = 0
    dir_plans: list[tuple[str, str]] = []
    if include_folders:
        dirs = list_paths(remote, base, dirs=True)
        dirs.sort(key=lambda d: d.count("/"), reverse=True)
        dir_plans = plan_renames(dirs, remove)
        print(f"\n[폴더] 대상 {len(dirs)}개 중 변경 대상 {len(dir_plans)}개")
        c2, s2 = apply_renames(remote, base, dir_plans, dry_run)

    if dry_run:
        total = len(file_plans) + len(dir_plans)
        print(f"\ndry-run 완료 — 총 {total}건 변경 예정. 확인 후 --dry-run 빼고 재실행하세요.")
    else:
        print(f"\nrename 완료 — 변경:{c1 + c2}  실패/skip:{s1 + s2}")
