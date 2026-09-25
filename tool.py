#!/usr/bin/env python3
"""
1. 사전 준비
   brew install rclone									# rclone 설치
   rclone config									# rclone 설정 셋팅 (원격 이름: pikpak)
   rclone lsf pikpak:/									# rclone 설정 확인

2. 사용법
   python pikpak_tool.py {--remote 원격이름} [rename | download | scan | delete | purge | clean] [파라미터]

3. 파라미터 설명
   3.1. 기본
        --remote: rclone 원격 이름이 pikpak이 아닌 경우에 지정 (콜론 유무 무관)
        --dry-run: 실제 실행 전 처리 결과 검증 (rename / download / delete / purge)
   3.2. rename
        -f: [필수] 대상 경로
        -r: [필수] 제거할 문자열
        --include-folders: [선택] 폴더명 변경 여부
   3.3. download
        -f: [필수] 대상 경로 (--from 과 배타적)
        --from: [선택] 다운로드 대상 경로 목록 파일 (라인당 전체 경로, -f 와 배타적)
        --transfers: [선택] 동시 전송 갯수 지정
        ※ 다운로드 결과는 항상 로컬 ./output 에 저장 (기존 폴더는 삭제 후 재생성)
        ※ -f 와 --from 은 동시에 사용 불가
   3.4. scan
        모든 파일을 스캔하여 ./output 에 결과 저장 (기존 폴더는 삭제 후 재생성)
        - 인자 없음  : 확장자 요약
            · results.txt      : 확장자별 파일 수 (예: "jpg: 123 files"), 확장자명 알파벳 순
            · no_extensions.txt: 확장자 없는 파일의 경로 목록 (해당 파일이 있을 때만 생성)
        - 인자 있음  : 지정 확장자별 경로 목록 (예: scan zip rar)
            · {ext}.txt        : 해당 확장자 파일의 경로 목록 (해당 파일이 있을 때만 생성)
            · 확장자는 점(.)/대소문자 무관
   3.5. delete / purge
        지정한 확장자의 파일을 제거. delete=휴지통 이동 / purge=완전 삭제(휴지통 미경유)
        - 확장자 인자 : 원격을 스캔해 해당 확장자 파일 삭제 (점/대소문자 무관, --dry-run 지원)
        - --from PATH : 경로 목록 파일(예: ./output/zip.txt)의 파일들을 삭제 (--dry-run 미지원)
        ※ 확장자 인자와 --from 은 동시에 사용 불가, 둘 중 하나는 반드시 지정
   3.6. clean
        원격 전체를 검사하여 파일이 없는 빈 폴더를 완전 삭제 (휴지통 미경유)
        하위→상위로 연쇄 삭제하며 원격 루트 자체는 보존
        --dry-run: 삭제 예정 빈 폴더만 표시하고 실제로는 삭제하지 않음

4. 사용 예시
   python pikpak_tool.py rename -f "/Movies/2024" -r "광고" --dry-run			# '광고' 문자열 제거 결과 확인
   python pikpak_tool.py rename -f "/Movies/2024" -r "광고"				# 파일명에서 '광고' 제거
   python pikpak_tool.py rename -f "/Movies/2024" -r "광고" --include-folders		# 폴더명까지 '광고' 제거
   python pikpak_tool.py download -f "/내 자료/2024" --dry-run				# 다운로드 대상 파일 확인
   python pikpak_tool.py download -f "/내 자료/2024"					# ./output 에 동일 구조로 다운로드
   python pikpak_tool.py download -f "/Movies/드라마" --transfers 6			# 동시 전송 6개로 제한하여 다운로드
   python pikpak_tool.py download --from ./targets.txt					# 목록 파일의 파일들을 ./output 에 다운로드
   python pikpak_tool.py download --from ./targets.txt --dry-run			# 목록 기반 다운로드 대상 확인
   python pikpak_tool.py scan								# 확장자 요약(results.txt / no_extensions.txt) 저장
   python pikpak_tool.py scan zip rar							# zip.txt, rar.txt 에 각 확장자 파일 경로 목록 저장
   python pikpak_tool.py delete asc sig							# .asc/.sig 파일을 휴지통으로 이동
   python pikpak_tool.py delete --from ./output/zip.txt					# 목록 파일의 파일들을 휴지통으로 이동
   python pikpak_tool.py purge asc sig --dry-run					# 완전 삭제 대상만 미리 확인
   python pikpak_tool.py purge asc sig							# .asc/.sig 파일을 완전 삭제
   python pikpak_tool.py purge --from ./output/zip.txt					# 목록 파일의 파일들을 완전 삭제
   python pikpak_tool.py clean --dry-run						# 삭제 예정 빈 폴더만 미리 확인
   python pikpak_tool.py clean								# 원격 전체의 빈 폴더를 완전 삭제
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import List, Tuple


# 다운로드/스캔 결과가 저장되는 고정 로컬 폴더
OUTPUT_DIR = "./output"


# ---------------------------------------------------------------------------
# rclone 실행 헬퍼
# ---------------------------------------------------------------------------

def run_rclone(args: List[str], capture: bool = True) -> str:
    """
    rclone 실행.
    capture=True  : stdout을 문자열로 반환(lsf/moveto 등).
    capture=False : 진행률을 그대로 터미널에 흘려보냄(copy -P 등).
    실패 시 stderr 출력하고 종료.
    """
    try:
        if capture:
            proc = subprocess.run(
                ["rclone", *args], capture_output=True, text=True, check=True
            )
            return proc.stdout
        subprocess.run(["rclone", *args], check=True)
        return ""
    except FileNotFoundError:
        sys.exit("rclone 을 찾을 수 없습니다. 'brew install rclone' 후 다시 시도하세요.")
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or "").strip() if capture else ""
        sys.exit(f"rclone 실행 실패:\n{stderr or e}")


def run_rclone_stream(args: List[str]):
    """rclone 을 실행하고 stdout 을 한 줄씩 yield (대용량 계정 대비 스트리밍)"""
    try:
        proc = subprocess.Popen(
            ["rclone", *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
    except FileNotFoundError:
        sys.exit("rclone 을 찾을 수 없습니다. 'brew install rclone' 후 다시 시도하세요.")

    for line in proc.stdout:
        path = line.strip()
        if path:
            yield path

    proc.wait()
    if proc.returncode != 0:
        err = proc.stderr.read()
        sys.exit(f"rclone 실행 실패 (code {proc.returncode}):\n{err}")


# ---------------------------------------------------------------------------
# 공통 유틸
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# DOWNLOAD 기능
# ---------------------------------------------------------------------------

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
            args = ["copy", f"{remote}:", OUTPUT_DIR,
                    "--files-from", tmp_path,
                    "--transfers", str(transfers), "-P"]
            if dry_run:
                args.append("--dry-run")

            print(f"[download] 목록 '{files_from}'의 {len(targets)}개 파일  ->  {OUTPUT_DIR}"
                  f"  (transfers={transfers}{', DRY-RUN' if dry_run else ''})")
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

    print(f"[download] {src}  ->  {dest}  (transfers={transfers}"
          f"{', DRY-RUN' if dry_run else ''})")
    run_rclone(args, capture=False)  # 진행률 실시간 출력
    print("[download] 완료" + (" (dry-run: 실제 전송 없음)" if dry_run else ""))


# ---------------------------------------------------------------------------
# RENAME 기능
# ---------------------------------------------------------------------------

def list_paths(remote: str, base: str, dirs: bool) -> List[str]:
    """base 하위 상대경로 목록. dirs=False→파일만, True→폴더만."""
    flag = "--dirs-only" if dirs else "--files-only"
    out = run_rclone(["lsf", "-R", flag, "--format", "p", f"{remote}:{base}"])
    return [line.rstrip("/") for line in out.splitlines() if line.strip()]


def plan_renames(rel_paths: List[str], remove: str) -> List[Tuple[str, str]]:
    """(old_rel, new_rel) 목록. 이름(basename)에서만 문자열 제거."""
    plans: List[Tuple[str, str]] = []
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
    remote: str, base: str, plans: List[Tuple[str, str]], dry_run: bool
) -> Tuple[int, int]:
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


def run_rename(
    remote: str, folder: str, remove: str, include_folders: bool, dry_run: bool
) -> None:
    remote = normalize_remote(remote)
    base = folder.strip().strip("/")

    # 1) 파일
    files = list_paths(remote, base, dirs=False)
    file_plans = plan_renames(files, remove)
    print(f"[파일] 대상 {len(files)}개 중 변경 대상 {len(file_plans)}개")
    c1, s1 = apply_renames(remote, base, file_plans, dry_run)

    # 2) 폴더(옵션) — 깊은 경로부터 처리해 상위 변경으로 하위 경로가 깨지지 않게
    c2 = s2 = 0
    dir_plans: List[Tuple[str, str]] = []
    if include_folders:
        dirs = list_paths(remote, base, dirs=True)
        dirs.sort(key=lambda d: d.count("/"), reverse=True)
        dir_plans = plan_renames(dirs, remove)
        print(f"\n[폴더] 대상 {len(dirs)}개 중 변경 대상 {len(dir_plans)}개")
        c2, s2 = apply_renames(remote, base, dir_plans, dry_run)

    if dry_run:
        total = len(file_plans) + len(dir_plans)
        print(f"\ndry-run 완료 — 총 {total}건 변경 예정. "
              f"확인 후 --dry-run 빼고 재실행하세요.")
    else:
        print(f"\nrename 완료 — 변경:{c1 + c2}  실패/skip:{s1 + s2}")


# ---------------------------------------------------------------------------
# SCAN 기능 (확장자 추출)
# ---------------------------------------------------------------------------

def collect_extensions(remote: str):
    """
    모든 파일을 스캔하여 두 가지를 수집. (요약 모드용)
      ext_counts   : {확장자(소문자): 파일 수}
      no_ext_paths : 확장자 없는 파일의 경로(remote 기준 상대경로) 목록
    """
    ext_counts: dict[str, int] = {}
    no_ext_paths: List[str] = []
    file_count = 0

    for path in run_rclone_stream(["lsf", "--recursive", "--files-only", f"{remote}:"]):
        file_count += 1
        suffix = Path(path).suffix  # 예: ".MP4"
        if suffix:
            ext = suffix.lstrip(".").lower()  # 소문자 통일
            ext_counts[ext] = ext_counts.get(ext, 0) + 1
        else:
            no_ext_paths.append(path)

    return ext_counts, no_ext_paths, file_count


def collect_by_extensions(remote: str, extensions: List[str]):
    """
    지정한 확장자에 해당하는 파일 경로를 확장자별로 수집. (확장자별 추출 모드용)
      반환: {확장자(소문자): [경로, ...]}
    비교는 대/소문자 무관.
    """
    targets = {normalize_ext(e) for e in extensions}
    buckets: dict[str, List[str]] = {ext: [] for ext in targets}
    file_count = 0

    for path in run_rclone_stream(["lsf", "--recursive", "--files-only", f"{remote}:"]):
        file_count += 1
        suffix = Path(path).suffix.lstrip(".").lower()  # 소문자 변환 후 비교
        if suffix and suffix in targets:
            buckets[suffix].append(path)

    return buckets, file_count


def run_scan(remote: str, extensions: List[str]) -> None:
    remote = normalize_remote(remote)

    # 확장자 인자가 없으면 기존 요약 모드
    if not extensions:
        _run_scan_summary(remote)
    else:
        _run_scan_by_extensions(remote, extensions)


def _run_scan_summary(remote: str) -> None:
    """인자 없는 scan: results.txt + no_extensions.txt 생성"""
    print(f"[scan] '{remote}:' 파일 목록 조회 중...")
    ext_counts, no_ext_paths, file_count = collect_extensions(remote)
    print(f"[scan] 총 {file_count}개 파일 스캔, "
          f"고유 확장자 {len(ext_counts)}개, 무확장자 {len(no_ext_paths)}개")

    out_dir = reset_output_dir()

    # results.txt : 확장자별 파일 수 (확장자명 알파벳 오름차순)
    result_file = out_dir / "results.txt"
    lines = [f"{ext}: {count} files" for ext, count in sorted(ext_counts.items())]
    result_file.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    print(f"[scan] 저장 완료: {result_file.resolve()}")

    # no_extensions.txt : 확장자 없는 파일이 1개 이상일 때만 생성
    if no_ext_paths:
        no_ext_file = out_dir / "no_extensions.txt"
        no_ext_file.write_text("\n".join(no_ext_paths) + "\n", encoding="utf-8")
        print(f"[scan] 저장 완료: {no_ext_file.resolve()}")


def _run_scan_by_extensions(remote: str, extensions: List[str]) -> None:
    """인자 있는 scan: 지정 확장자별로 {ext}.txt 생성 (해당 파일이 있을 때만)"""
    exts = [normalize_ext(e) for e in extensions]

    # 요약 모드의 예약 파일명과 충돌하는 확장자는 거부 (출력 파일 오염 방지)
    reserved = {"results", "no_extensions"}
    conflict = reserved & set(exts)
    if conflict:
        sys.exit(f"[ERROR] 예약어는 확장자로 사용할 수 없습니다: {sorted(conflict)} "
                 f"(예약어: {sorted(reserved)})")

    print(f"[scan] '{remote}:'에서 확장자 {exts} 파일 검색 중...")
    buckets, file_count = collect_by_extensions(remote, exts)
    print(f"[scan] 총 {file_count}개 파일 스캔")

    out_dir = reset_output_dir()

    # {ext}.txt : 해당 확장자 파일이 1개 이상일 때만 생성. 내용은 경로 목록.
    for ext in sorted(buckets):
        paths = buckets[ext]
        if not paths:
            print(f"[scan] '{ext}': 대상 없음 (파일 미생성)")
            continue
        ext_file = out_dir / f"{ext}.txt"
        ext_file.write_text("\n".join(paths) + "\n", encoding="utf-8")
        print(f"[scan] 저장 완료: {ext_file.resolve()} ({len(paths)}개)")


# ---------------------------------------------------------------------------
# DELETE / PURGE 기능 (지정 확장자 파일 제거)
# ---------------------------------------------------------------------------

def list_matching(remote: str, extensions: List[str]) -> List[str]:
    """확장자를 소문자로 변환해 비교하여 매칭되는 파일 경로 목록 반환"""
    targets = {normalize_ext(e) for e in extensions}
    matched: List[str] = []

    for path in run_rclone_stream(["lsf", "--recursive", "--files-only", f"{remote}:"]):
        suffix = Path(path).suffix.lstrip(".").lower()  # 소문자 변환 후 비교
        if suffix and suffix in targets:
            matched.append(path)

    return matched


def delete_files(remote: str, paths: List[str], permanent: bool) -> None:
    """--files-from 으로 매칭 파일을 일괄 삭제. permanent=True 면 휴지통 미경유(완전 삭제)"""
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write("\n".join(paths) + "\n")
            tmp_path = f.name

        args = ["delete", f"{remote}:", "--files-from", tmp_path]
        # PikPak 삭제 정책: use-trash=true(휴지통 이동) / false(완전 삭제)
        args.append(f"--pikpak-use-trash={'false' if permanent else 'true'}")
        run_rclone(args, capture=False)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


def load_paths_from_file(files_from: str) -> List[str]:
    """--from 파일에서 경로 목록을 읽어 반환 (빈 줄 제거)"""
    p = Path(files_from).expanduser()
    if not p.is_file():
        sys.exit(f"[ERROR] 목록 파일을 찾을 수 없습니다: {files_from}")
    lines = p.read_text(encoding="utf-8").splitlines()
    return [ln.strip() for ln in lines if ln.strip()]


def run_removal(
    remote: str,
    extensions: List[str],
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
            print("[WARN] --from 모드에서는 --dry-run 이 적용되지 않습니다. 실제 삭제를 진행합니다.")
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


# ---------------------------------------------------------------------------
# CLEAN 기능 (빈 폴더 완전 삭제)
# ---------------------------------------------------------------------------

def run_clean(remote: str, dry_run: bool) -> None:
    """원격 전체를 검사하여 빈 폴더를 완전 삭제 (하위→상위 연쇄, 루트는 보존)"""
    remote = normalize_remote(remote)
    print(f"[clean] '{remote}:' 빈 폴더 검사 중..."
          f"{' (DRY-RUN)' if dry_run else ''}")

    # rmdirs: 비어 있는 디렉터리를 하위→상위 순으로 모두 제거
    #   --leave-root       : 원격 루트 자체는 삭제하지 않음
    #   --pikpak-use-trash : false → 완전 삭제(휴지통 미경유)
    args = [
        "rmdirs", f"{remote}:",
        "--leave-root",
        "--pikpak-use-trash=false",
    ]
    if dry_run:
        # 삭제 예정 폴더를 rclone 로그로 미리 표시 (실제 삭제 없음)
        args += ["--dry-run", "-v"]

    run_rclone(args, capture=False)
    print("[clean] 완료" + (" (dry-run: 실제 삭제 없음)" if dry_run else ""))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pikpak_tool.py",
        description="PikPak 통합 도구 (rclone 기반: download / rename / scan / delete / purge)",
    )
    p.add_argument("--remote", default="pikpak",
                   help="rclone 원격 이름 (기본: pikpak, 콜론 유무 무관)")

    sub = p.add_subparsers(dest="command", required=True)

    # download
    d = sub.add_parser("download", help="폴더 또는 목록 파일 기준으로 로컬 ./output 에 다운로드")
    d.add_argument("-f", "--folder", default="",
                   help='대상 폴더 경로. 예: "/내 자료/2024" (루트는 빈값). --from 과 배타적')
    d.add_argument("--from", dest="files_from", metavar="PATH",
                   help="다운로드 대상 경로 목록 파일 (라인당 전체 경로). -f 와 배타적")
    d.add_argument("--transfers", type=int, default=4,
                   help="동시 다운로드 수 (기본 4)")
    d.add_argument("--dry-run", action="store_true",
                   help="실제 전송 없이 대상만 확인")

    # rename
    r = sub.add_parser("rename", help="파일명에서 문자열 제거")
    r.add_argument("-f", "--folder", default="",
                   help='대상 폴더 경로. 예: "/Movies/2024" (루트는 빈값)')
    r.add_argument("-r", "--remove", required=True,
                   help="파일명에서 제거할 문자열")
    r.add_argument("--include-folders", action="store_true",
                   help="파일뿐 아니라 하위 폴더 이름도 변경")
    r.add_argument("--dry-run", action="store_true",
                   help="실제 변경 없이 변경 예정 목록만 출력(최초 1회 권장)")

    # scan
    sc = sub.add_parser(
        "scan",
        help="인자 없으면 확장자 요약(results/no_extensions), "
             "인자 있으면 지정 확장자별 경로 목록({ext}.txt) 생성",
    )
    sc.add_argument("extensions", nargs="*",
                    help="추출할 확장자 목록 (예: zip rar). 생략 시 요약 모드. 점(.)/대소문자 무관")

    # delete (휴지통 이동)
    de = sub.add_parser("delete", help="지정 확장자 파일을 휴지통으로 이동")
    de.add_argument("extensions", nargs="*",
                    help="대상 확장자 목록 (예: asc sig). 점(.)/대소문자 무관")
    de.add_argument("--from", dest="files_from", metavar="PATH",
                    help="삭제 대상 경로 목록 파일 (예: ./output/zip.txt). 확장자 인자와 배타적")
    de.add_argument("--dry-run", action="store_true",
                    help="대상만 표시하고 실제로는 삭제하지 않음 (--from 모드에서는 무시됨)")

    # purge (완전 삭제)
    pu = sub.add_parser("purge", help="지정 확장자 파일을 완전 삭제 (휴지통 미경유)")
    pu.add_argument("extensions", nargs="*",
                    help="대상 확장자 목록 (예: asc sig). 점(.)/대소문자 무관")
    pu.add_argument("--from", dest="files_from", metavar="PATH",
                    help="삭제 대상 경로 목록 파일 (예: ./output/zip.txt). 확장자 인자와 배타적")
    pu.add_argument("--dry-run", action="store_true",
                    help="대상만 표시하고 실제로는 삭제하지 않음 (--from 모드에서는 무시됨)")

    # clean (빈 폴더 완전 삭제)
    cl = sub.add_parser("clean", help="원격 전체의 빈 폴더를 완전 삭제 (하위→상위 연쇄, 루트 보존)")
    cl.add_argument("--dry-run", action="store_true",
                    help="삭제 예정 빈 폴더만 표시하고 실제로는 삭제하지 않음")

    return p


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "download":
        run_download(args.remote, args.folder, args.transfers, args.dry_run,
                     files_from=args.files_from)
    elif args.command == "rename":
        run_rename(args.remote, args.folder, args.remove,
                   args.include_folders, args.dry_run)
    elif args.command == "scan":
        run_scan(args.remote, args.extensions)
    elif args.command == "delete":
        run_removal(args.remote, args.extensions, permanent=False,
                    dry_run=args.dry_run, files_from=args.files_from)
    elif args.command == "purge":
        run_removal(args.remote, args.extensions, permanent=True,
                    dry_run=args.dry_run, files_from=args.files_from)
    elif args.command == "clean":
        run_clean(args.remote, args.dry_run)


if __name__ == "__main__":
    main()
