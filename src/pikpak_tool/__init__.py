"""
PikPak 통합 도구 (rclone 기반)

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
