"""SCAN 기능 (확장자 추출)"""

from __future__ import annotations

import sys
from pathlib import Path

from pikpak_tool.rclone import run_rclone_stream
from pikpak_tool.utils import normalize_ext, normalize_remote, reset_output_dir


def collect_extensions(remote: str):
    """
    모든 파일을 스캔하여 두 가지를 수집. (요약 모드용)
      ext_counts   : {확장자(소문자): 파일 수}
      no_ext_paths : 확장자 없는 파일의 경로(remote 기준 상대경로) 목록
    """
    ext_counts: dict[str, int] = {}
    no_ext_paths: list[str] = []
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


def collect_by_extensions(remote: str, extensions: list[str]):
    """
    지정한 확장자에 해당하는 파일 경로를 확장자별로 수집. (확장자별 추출 모드용)
      반환: {확장자(소문자): [경로, ...]}
    비교는 대/소문자 무관.
    """
    targets = {normalize_ext(e) for e in extensions}
    buckets: dict[str, list[str]] = {ext: [] for ext in targets}
    file_count = 0

    for path in run_rclone_stream(["lsf", "--recursive", "--files-only", f"{remote}:"]):
        file_count += 1
        suffix = Path(path).suffix.lstrip(".").lower()  # 소문자 변환 후 비교
        if suffix and suffix in targets:
            buckets[suffix].append(path)

    return buckets, file_count


def run_scan(remote: str, extensions: list[str]) -> None:
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
    print(
        f"[scan] 총 {file_count}개 파일 스캔, "
        f"고유 확장자 {len(ext_counts)}개, 무확장자 {len(no_ext_paths)}개"
    )

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


def _run_scan_by_extensions(remote: str, extensions: list[str]) -> None:
    """인자 있는 scan: 지정 확장자별로 {ext}.txt 생성 (해당 파일이 있을 때만)"""
    exts = [normalize_ext(e) for e in extensions]

    # 요약 모드의 예약 파일명과 충돌하는 확장자는 거부 (출력 파일 오염 방지)
    reserved = {"results", "no_extensions"}
    conflict = reserved & set(exts)
    if conflict:
        sys.exit(
            f"[ERROR] 예약어는 확장자로 사용할 수 없습니다: {sorted(conflict)} "
            f"(예약어: {sorted(reserved)})"
        )

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
