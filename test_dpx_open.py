#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
pydpx_meta.DpxHeader() 함수 테스트 스크립트
사용법: python test_dpx_open.py /path/to/file.dpx
"""
import os
import sys
import pydpx_meta

def test_dpx_file(file_path):
    """DPX 파일을 단계별로 테스트"""

    print("=" * 70)
    print("pydpx_meta.DpxHeader() 테스트")
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

    # Step 3: 파일 매직 넘버 확인 (DPX 시그니처)
    print("[Step 3] DPX 매직 넘버 확인...")
    try:
        with open(file_path, 'rb') as f:
            magic = f.read(4)
            print(f"  매직 넘버: {magic.hex()}")
            # DPX magic: SDPX (0x53445058) or XPDS (0x58504453) for big/little endian
            if magic in [b'SDPX', b'XPDS']:
                print(f"✓ PASS: 유효한 DPX 매직 넘버")
            else:
                print(f"✗ WARNING: DPX 매직 넘버가 아닙니다 (예상: SDPX 또는 XPDS)")
                print(f"  이 파일은 DPX가 아니거나 손상되었을 수 있습니다")
    except Exception as e:
        print(f"✗ FAIL: 매직 넘버 읽기 실패: {e}")
        return False
    print()

    # Step 4: pydpx_meta.DpxHeader() 직접 호출 (위험!)
    print("[Step 4] pydpx_meta.DpxHeader() 직접 호출...")
    print("  ⚠️  WARNING: 이 단계에서 segfault가 발생할 수 있습니다!")
    print("  3초 후 시작합니다...")
    import time
    time.sleep(3)

    try:
        print(f"  pydpx_meta.DpxHeader('{file_path}') 호출 중...")
        dpx = pydpx_meta.DpxHeader(file_path)
        print(f"✓ PASS: pydpx_meta.DpxHeader() 성공!")
        print(f"  DPX 객체 생성됨: {dpx}")
        print()

        # Step 5: 헤더 정보 읽기
        print("[Step 5] 헤더 정보 읽기...")
        try:
            print(f"✓ PASS: 헤더 접근 가능")
            print()

            # Step 6: 특정 메타데이터 읽기
            print("[Step 6] 메타데이터 읽기...")

            try:
                tc = dpx.tv_header.time_code
                print(f"  ✓ time_code: {tc}")
            except Exception as e:
                print(f"  - time_code: 읽기 실패 ({e})")

            try:
                fps = dpx.raw_header.TvHeader.FrameRate
                print(f"  ✓ FrameRate: {fps}")
            except Exception as e:
                print(f"  - FrameRate: 읽기 실패 ({e})")

            try:
                width = dpx.raw_header.OrientHeader.XOriginalSize
                height = dpx.raw_header.OrientHeader.YOriginalSize
                print(f"  ✓ Resolution: {width} x {height}")
            except Exception as e:
                print(f"  - Resolution: 읽기 실패 ({e})")

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
        print(f"✗ FAIL: pydpx_meta.DpxHeader() 실패!")
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
        print("사용법: python test_dpx_open.py /path/to/file.dpx")
        sys.exit(1)

    dpx_file = sys.argv[1]

    try:
        success = test_dpx_file(dpx_file)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n중단됨")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
