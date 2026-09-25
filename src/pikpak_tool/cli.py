"""CLI (argparse 파서 + 서브커맨드 디스패치)"""

from __future__ import annotations

import argparse

from pikpak_tool.commands.clean import run_clean
from pikpak_tool.commands.download import run_download
from pikpak_tool.commands.remove import run_removal
from pikpak_tool.commands.rename import run_rename
from pikpak_tool.commands.scan import run_scan


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pikpak_tool.py",
        description="PikPak 통합 도구 (rclone 기반: download / rename / scan / delete / purge)",
    )
    p.add_argument(
        "--remote", default="pikpak", help="rclone 원격 이름 (기본: pikpak, 콜론 유무 무관)"
    )

    sub = p.add_subparsers(dest="command", required=True)

    # download
    d = sub.add_parser("download", help="폴더 또는 목록 파일 기준으로 로컬 ./output 에 다운로드")
    d.add_argument(
        "-f",
        "--folder",
        default="",
        help='대상 폴더 경로. 예: "/내 자료/2024" (루트는 빈값). --from 과 배타적',
    )
    d.add_argument(
        "--from",
        dest="files_from",
        metavar="PATH",
        help="다운로드 대상 경로 목록 파일 (라인당 전체 경로). -f 와 배타적",
    )
    d.add_argument("--transfers", type=int, default=4, help="동시 다운로드 수 (기본 4)")
    d.add_argument("--dry-run", action="store_true", help="실제 전송 없이 대상만 확인")

    # rename
    r = sub.add_parser("rename", help="파일명에서 문자열 제거")
    r.add_argument(
        "-f", "--folder", default="", help='대상 폴더 경로. 예: "/Movies/2024" (루트는 빈값)'
    )
    r.add_argument("-r", "--remove", required=True, help="파일명에서 제거할 문자열")
    r.add_argument(
        "--include-folders", action="store_true", help="파일뿐 아니라 하위 폴더 이름도 변경"
    )
    r.add_argument(
        "--dry-run", action="store_true", help="실제 변경 없이 변경 예정 목록만 출력(최초 1회 권장)"
    )

    # scan
    sc = sub.add_parser(
        "scan",
        help="인자 없으면 확장자 요약(results/no_extensions), "
        "인자 있으면 지정 확장자별 경로 목록({ext}.txt) 생성",
    )
    sc.add_argument(
        "extensions",
        nargs="*",
        help="추출할 확장자 목록 (예: zip rar). 생략 시 요약 모드. 점(.)/대소문자 무관",
    )

    # delete (휴지통 이동)
    de = sub.add_parser("delete", help="지정 확장자 파일을 휴지통으로 이동")
    de.add_argument(
        "extensions", nargs="*", help="대상 확장자 목록 (예: asc sig). 점(.)/대소문자 무관"
    )
    de.add_argument(
        "--from",
        dest="files_from",
        metavar="PATH",
        help="삭제 대상 경로 목록 파일 (예: ./output/zip.txt). 확장자 인자와 배타적",
    )
    de.add_argument(
        "--dry-run",
        action="store_true",
        help="대상만 표시하고 실제로는 삭제하지 않음 (--from 모드에서는 무시됨)",
    )

    # purge (완전 삭제)
    pu = sub.add_parser("purge", help="지정 확장자 파일을 완전 삭제 (휴지통 미경유)")
    pu.add_argument(
        "extensions", nargs="*", help="대상 확장자 목록 (예: asc sig). 점(.)/대소문자 무관"
    )
    pu.add_argument(
        "--from",
        dest="files_from",
        metavar="PATH",
        help="삭제 대상 경로 목록 파일 (예: ./output/zip.txt). 확장자 인자와 배타적",
    )
    pu.add_argument(
        "--dry-run",
        action="store_true",
        help="대상만 표시하고 실제로는 삭제하지 않음 (--from 모드에서는 무시됨)",
    )

    # clean (빈 폴더 완전 삭제)
    cl = sub.add_parser("clean", help="원격 전체의 빈 폴더를 완전 삭제 (하위→상위 연쇄, 루트 보존)")
    cl.add_argument(
        "--dry-run", action="store_true", help="삭제 예정 빈 폴더만 표시하고 실제로는 삭제하지 않음"
    )

    return p


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "download":
        run_download(
            args.remote, args.folder, args.transfers, args.dry_run, files_from=args.files_from
        )
    elif args.command == "rename":
        run_rename(args.remote, args.folder, args.remove, args.include_folders, args.dry_run)
    elif args.command == "scan":
        run_scan(args.remote, args.extensions)
    elif args.command == "delete":
        run_removal(
            args.remote,
            args.extensions,
            permanent=False,
            dry_run=args.dry_run,
            files_from=args.files_from,
        )
    elif args.command == "purge":
        run_removal(
            args.remote,
            args.extensions,
            permanent=True,
            dry_run=args.dry_run,
            files_from=args.files_from,
        )
    elif args.command == "clean":
        run_clean(args.remote, args.dry_run)
