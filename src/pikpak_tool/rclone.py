"""rclone 실행 헬퍼"""

from __future__ import annotations

import subprocess
import sys


def run_rclone(args: list[str], capture: bool = True) -> str:
    """
    rclone 실행.
    capture=True  : stdout을 문자열로 반환(lsf/moveto 등).
    capture=False : 진행률을 그대로 터미널에 흘려보냄(copy -P 등).
    실패 시 stderr 출력하고 종료.
    """
    try:
        if capture:
            proc = subprocess.run(["rclone", *args], capture_output=True, text=True, check=True)
            return proc.stdout
        subprocess.run(["rclone", *args], check=True)
        return ""
    except FileNotFoundError:
        sys.exit("rclone 을 찾을 수 없습니다. 'brew install rclone' 후 다시 시도하세요.")
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or "").strip() if capture else ""
        sys.exit(f"rclone 실행 실패:\n{stderr or e}")


def run_rclone_stream(args: list[str]):
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
