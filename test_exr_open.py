#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OpenEXR.InputFile() 함수 테스트 스크립트
사용법: python test_exr_open.py /path/to/file.exr
"""
import os
import sys
import OpenEXR

def test_exr_file(file_path):
    """EXR 파일을 단계별로 테스트"""

    print("=" * 70)
    print("OpenEXR.InputFile() 테스트")
    print("=" * 70)
    print(f"테스트 파일: {file_path}")
    print()

    # Step 1: 파일 존재 확인
    print("[Step 1] 파일 존재 확인...")
    if not os.path.exists(file_path):
        print(f"✗ FAIL: 파일이 존재하지 않습니다: {file_path}")
        return False
    print(f"✓ PASS: 파일 존재함")
    print(f"  파일 크기: {os.path.getsize(file_path)} bytes")
    print()

    # Step 2: 파일 읽기 권한 확인
    print("[Step 2] 파일 읽기 권한 확인...")
    if not os.access(file_path, os.R_OK):
        print(f"✗ FAIL: 파일 읽기 권한 없음")
        return False
    print(f"✓ PASS: 읽기 권한 있음")
    print()

    # Step 3: 파일 매직 넘버 확인 (EXR 시그니처)
    print("[Step 3] EXR 매직 넘버 확인...")
    try:
        with open(file_path, 'rb') as f:
            magic = f.read(4)
            print(f"  매직 넘버: {magic.hex()}")
            if magic == b'\x76\x2f\x31\x01':
                print(f"✓ PASS: 유효한 EXR 매직 넘버")
            else:
                print(f"✗ WARNING: EXR 매직 넘버가 아닙니다 (예상: 762f3101)")
                print(f"  이 파일은 EXR이 아니거나 손상되었을 수 있습니다")
    except Exception as e:
        print(f"✗ FAIL: 매직 넘버 읽기 실패: {e}")
        return False
    print()

    # Step 4: OpenEXR.InputFile() 직접 호출 (위험!)
    print("[Step 4] OpenEXR.InputFile() 직접 호출...")
    print("  ⚠️  WARNING: 이 단계에서 segfault가 발생할 수 있습니다!")
    print("  3초 후 시작합니다...")
    import time
    time.sleep(3)

    try:
        print(f"  OpenEXR.InputFile('{file_path}') 호출 중...")
        exr = OpenEXR.InputFile(file_path)
        print(f"✓ PASS: OpenEXR.InputFile() 성공!")
        print(f"  EXR 객체 생성됨: {exr}")
        print()

        # Step 5: 헤더 정보 읽기
        print("[Step 5] 헤더 정보 읽기...")
        try:
            header = exr.header()
            print(f"✓ PASS: 헤더 읽기 성공")
            print(f"  헤더 키 개수: {len(header)} 개")
            print(f"  헤더 키 목록:")
            for key in sorted(header.keys()):
                print(f"    - {key}")
            print()

            # Step 6: 특정 메타데이터 읽기
            print("[Step 6] 메타데이터 읽기...")

            if "timeCode" in header:
                tc = header['timeCode']
                print(f"  ✓ timeCode: {tc.hours:02d}:{tc.minutes:02d}:{tc.seconds:02d}:{tc.frame:02d}")
            else:
                print(f"  - timeCode: 없음")

            if "framesPerSecond" in header:
                fps = header['framesPerSecond']
                print(f"  ✓ framesPerSecond: {float(fps.n)/float(fps.d)}")
            else:
                print(f"  - framesPerSecond: 없음")

            if "dataWindow" in header:
                dw = header['dataWindow']
                print(f"  ✓ dataWindow: {dw.max.x+1} x {dw.max.y+1}")
            else:
                print(f"  - dataWindow: 없음")

            print()
            print("=" * 70)
            print("✓ 모든 테스트 통과!")
            print("=" * 70)
            return True

        except Exception as e:
            print(f"✗ FAIL: 헤더 읽기 실패: {e}")
            import traceback
            traceback.print_exc()
            return False

    except Exception as e:
        print(f"✗ FAIL: OpenEXR.InputFile() 실패!")
        print(f"  예외 타입: {type(e).__name__}")
        print(f"  예외 메시지: {e}")
        import traceback
        traceback.print_exc()
        print()
        print("=" * 70)
        print("이 예외는 Python에서 잡혔습니다.")
        print("만약 segfault가 발생했다면 이 메시지는 보이지 않습니다.")
        print("=" * 70)
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python test_exr_open.py /path/to/file.exr")
        sys.exit(1)

    exr_file = sys.argv[1]

    try:
        success = test_exr_file(exr_file)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n중단됨")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
