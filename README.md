# pikpak-tool

[rclone](https://rclone.org/)으로 PikPak 원격 저장소를 관리하는 CLI 도구입니다.
파일명 일괄 변경, 다운로드, 확장자 스캔, 확장자별 삭제, 빈 폴더 정리를 지원합니다.

## 사전 준비

```bash
brew install rclone          # rclone 설치
rclone config                # 원격 설정 (기본 원격 이름: pikpak)
rclone lsf pikpak:/          # 설정 확인
```

[uv](https://docs.astral.sh/uv/)가 필요합니다. Python 3.14.7은 `.python-version`에 고정되어 있어 uv가 자동으로 사용합니다.

## 설치

```bash
uv sync                      # .venv 생성 + 의존성(개발용 포함) 설치
```

전역 명령으로 설치하려면:

```bash
uv tool install .            # 어디서든 `pikpak-tool` 실행 가능
```

## 실행

```bash
uv run pikpak-tool --help
uv run pikpak-tool [--remote 원격이름] <명령> [옵션]
# 또는
uv run python -m pikpak_tool <명령> [옵션]
```

`download`와 `scan`의 결과는 **현재 디렉터리의 `./output`** 에 저장됩니다. 실행할 때마다 기존 폴더를 지우고 새로 만듭니다(dry-run 제외).

### 명령

| 명령 | 설명 | 주요 옵션 |
|---|---|---|
| `rename` | 파일명(옵션: 폴더명)에서 문자열 제거 | `-f` 대상 경로, `-r` 제거할 문자열(필수), `--include-folders`, `--dry-run` |
| `download` | 폴더 또는 목록 파일 기준으로 `./output`에 다운로드 | `-f` 폴더 / `--from` 목록 파일(동시 사용 불가), `--transfers`, `--dry-run` |
| `scan` | 인자 없으면 확장자 요약, 확장자를 주면 확장자별 경로 목록 | `scan [ext ...]` |
| `delete` | 지정한 확장자의 파일을 휴지통으로 이동 | `delete ext ...` / `--from 목록`, `--dry-run`(확장자 모드만) |
| `purge` | 지정한 확장자의 파일을 완전 삭제(휴지통을 거치지 않음) | `delete`와 같음 |
| `clean` | 빈 폴더를 하위부터 상위로 완전 삭제(루트는 남김) | `--dry-run` |

공통 옵션: `--remote`는 원격 이름이 `pikpak`이 아닐 때 지정합니다(콜론은 붙여도 되고 빼도 됩니다).

### 예시

```bash
uv run pikpak-tool rename -f "/Movies/2024" -r "광고" --dry-run   # 변경 결과 미리 보기
uv run pikpak-tool rename -f "/Movies/2024" -r "광고" --include-folders
uv run pikpak-tool download -f "/내 자료/2024" --transfers 6
uv run pikpak-tool download --from ./targets.txt --dry-run
uv run pikpak-tool scan                                          # results.txt / no_extensions.txt
uv run pikpak-tool scan zip rar                                  # zip.txt, rar.txt
uv run pikpak-tool delete asc sig                                # 휴지통으로 이동
uv run pikpak-tool purge --from ./output/zip.txt                 # 목록 파일 기준 완전 삭제
uv run pikpak-tool clean --dry-run
```

> ⚠️ `delete`/`purge --from` 모드에서는 `--dry-run`이 적용되지 않고 바로 삭제됩니다.

## 개발

```bash
uv run pytest                # 테스트
uv run ruff check .          # lint
uv run ruff format .         # 포맷
```

VS Code에는 `.vscode/launch.json`에 실행/디버그 구성(인자 입력, scan, rename dry-run, clean dry-run, pytest)이 들어 있습니다.

## 구조

```
src/pikpak_tool/
├── __init__.py         # 패키지 (사용법 docstring)
├── __main__.py         # python -m pikpak_tool
├── cli.py              # argparse 파서 + 명령 디스패치 (entry point: main)
├── rclone.py           # rclone 실행 헬퍼 (run_rclone, run_rclone_stream)
├── utils.py            # 공통 유틸 (OUTPUT_DIR, 경로·확장자 정규화, 목록 파일 로드)
└── commands/
    ├── download.py
    ├── rename.py
    ├── scan.py
    ├── remove.py       # delete / purge
    └── clean.py
tests/                  # pytest
```
