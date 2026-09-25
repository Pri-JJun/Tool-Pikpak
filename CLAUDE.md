# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 개요

rclone을 subprocess로 호출해 PikPak 원격 저장소를 관리하는 CLI(`pikpak-tool`)입니다. 런타임 의존성은 없고(표준 라이브러리만 사용) 외부 요구사항은 `rclone` 바이너리와 rclone 원격 설정(기본 이름 `pikpak`)뿐입니다. uv + src layout, Python 3.14.7(`.python-version`)을 사용합니다.

사용자와는 한국어로 소통하고, 코드 주석·출력 메시지도 기존처럼 한국어를 유지합니다.

## 명령어

```bash
uv sync                                   # .venv 생성 + dev 의존성(pytest, ruff) 설치
uv run pikpak-tool <명령> [옵션]            # 실행 (또는 uv run python -m pikpak_tool)
uv run pytest                             # 전체 테스트
uv run pytest tests/test_rename.py::test_plan_renames_only_changes_basename   # 단일 테스트
uv run ruff check . && uv run ruff format .                                  # lint + format
```

## 구조

- `cli.py`: argparse 파서(`build_parser`)와 서브커맨드 디스패치(`main`, `[project.scripts]` 진입점)입니다. `commands/`의 `run_*` 함수를 호출합니다. `delete`와 `purge`는 모두 `commands/remove.py`의 `run_removal`을 쓰고 `permanent` 플래그만 다릅니다(`--pikpak-use-trash=true/false`).
- `rclone.py`: 모든 rclone 호출이 이곳을 거칩니다.
  - `run_rclone(capture=True)`: stdout을 문자열로 받습니다(lsf, moveto 등).
  - `run_rclone(capture=False)`: 진행률을 터미널에 그대로 출력합니다(copy -P, delete, rmdirs).
  - `run_rclone_stream`: `lsf` 결과를 한 줄씩 yield합니다(대용량 계정 대비).
  - 실패하면 `sys.exit`로 종료합니다. `rename`의 `apply_renames`는 이 `SystemExit`을 잡아 건별 실패로 집계하므로, 에러 처리 방식을 바꿀 때 주의해야 합니다.
- `utils.py`: `OUTPUT_DIR = "./output"`이 기준입니다. 이 경로는 **현재 작업 디렉터리 기준 상대경로**이고, `reset_output_dir()`는 기존 폴더를 통째로 삭제한 뒤 다시 만듭니다(download는 dry-run일 때 삭제하지 않음). 원격 이름은 `normalize_remote`로 콜론을 떼고 `f"{remote}:{path}"` 형식으로 조합합니다.
- 여러 파일을 한꺼번에 처리할 때(`download --from`, delete/purge)는 경로 목록을 임시 파일로 써서 rclone `--files-from`에 넘기고 `finally`에서 지웁니다.

## 동작 호환성

이 패키지는 원래 단일 스크립트 `tool.py`(첫 커밋에 보존됨)를 분리해 만든 것이고, 출력·종료 코드·rclone 인자는 원본과 동일하게 유지하는 것이 원칙입니다. argparse의 `prog="pikpak_tool.py"`도 원본 help 출력을 유지하려고 남겨 둔 것입니다. 이 동작을 바꾸는 것은 의도적인 변경일 때만 합니다.

- 실제 `pikpak:` 원격에 명령을 실행하면 파일이 삭제되거나 이름이 바뀔 수 있습니다. 검증은 `--dry-run`이나 가짜 `rclone` 스크립트를 PATH 앞에 두는 방식으로 합니다. `delete/purge --from` 모드는 `--dry-run`을 무시하고 실제로 삭제합니다.
- 테스트는 rclone을 호출하지 않는 순수 함수(`plan_renames`, `normalize_*`, 파서)만 대상으로 합니다.
- ruff: `__init__.py`의 사용법 docstring(탭 정렬)은 원본 그대로 보존하려고 E501을 예외 처리했습니다.

## Git

커밋 author/committer 이메일은 `haengjun.shin@gmail.com`으로 합니다. 커밋 메시지는 한국어로 쓰고, Co-Authored-By 줄은 이메일 없이 이름만 적습니다(예: `Co-Authored-By: Claude Opus 5.5`).
