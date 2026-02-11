#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Westworld IO-Manager

독립 실행 가능한 VFX 파이프라인 도구
Shot/Source 파일을 등록하고 관리합니다.
"""

import sys
import os
import subprocess
import argparse

# third-party/ 디렉토리를 sys.path에 추가 (tractor 등 번들 라이브러리)
_APP_DIR = os.path.dirname(os.path.abspath(__file__))
_THIRD_PARTY_DIR = os.path.join(_APP_DIR, 'third-party')
if os.path.isdir(_THIRD_PARTY_DIR) and _THIRD_PARTY_DIR not in sys.path:
    sys.path.insert(0, _THIRD_PARTY_DIR)


def get_rez_root_command():
    """Rez 루트 경로를 찾기 위한 명령어를 반환합니다."""
    return 'rez-env rez -- printenv REZ_REZ_ROOT'


def get_rez_module_root():
    """Rez 모듈 루트 경로를 반환합니다."""
    command = get_rez_root_command()
    try:
        module_path, stderr = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True
        ).communicate()

        module_path = module_path.strip()

        if not stderr and module_path:
            return module_path.decode('utf-8') if isinstance(module_path, bytes) else module_path
    except Exception as e:
        print(f"Failed to get Rez module root: {e}")

    return ''


def set_module_path(module_path):
    """모듈 경로를 sys.path에 추가합니다."""
    for module in module_path.split(":"):
        if module and module not in sys.path:
            sys.path.append(module)


def setup_rez_environment(config=None, packages=None):
    """
    Rez 환경을 설정합니다.

    Args:
        config: AppConfig 인스턴스 (선택사항)
        packages: 로드할 패키지 리스트 (선택사항, config보다 우선)

    Returns:
        bool: Rez 환경 설정 성공 여부

    Rez가 설치되어 있으면 필요한 패키지들을 로드합니다.
    Rez가 없으면 일반 pip 패키지를 사용합니다.
    """
    # Rez 사용 가능 여부 확인
    try:
        import rez as _
    except ImportError:
        rez_path = get_rez_module_root()
        if rez_path:
            sys.path.append(rez_path)
            print(f"Added Rez path to sys.path: {rez_path}")
        else:
            print("WARNING: Rez is not installed or not found in PATH")
            print("         Using pip packages instead (install from requirements.txt)")
            return False

    # Rez 환경 설정 시도
    try:
        from rez.resolved_context import ResolvedContext

        # 패키지 목록 결정 (우선순위: 인자 > 설정 > 기본값)
        if packages is None:
            if config:
                packages = config.get('rez.required_packages', [])
            if not packages:
                # 기본 패키지 목록 (fallback)
                packages = [
                    'tractor', 'pyseq', 'Xlrd', 'XlsxWriter',
                    'pydpx_meta', 'pyopenexr_tk', 'Pillow',
                    'timecode', 'ffmpeg', 'ffmpeg_python', 'edl'
                ]

        if not packages:
            print("WARNING: No Rez packages specified")
            return False

        print(f"Resolving Rez packages: {', '.join(packages)}")

        # 패키지 컨텍스트 생성
        try:
            context = ResolvedContext(packages)
        except Exception as resolve_error:
            print(f"ERROR: Failed to resolve Rez packages: {resolve_error}")
            print("       Some packages may not be available in the Rez repository")
            print("       Attempting to continue with pip packages...")
            return False

        # PYTHONPATH 설정
        try:
            env = context.get_environ()
            if 'PYTHONPATH' in env:
                module_path = env['PYTHONPATH']
                set_module_path(module_path)
                print(f"Set PYTHONPATH from Rez: {len(module_path.split(':'))} paths")
            else:
                print("WARNING: No PYTHONPATH in Rez context")
        except Exception as path_error:
            print(f"WARNING: Failed to set PYTHONPATH: {path_error}")

        # FFmpeg PATH 추가 (선택적)
        try:
            if 'ffmpeg' in packages:
                ffmpeg_context = ResolvedContext(['ffmpeg'])
                ffmpeg_env = ffmpeg_context.get_environ()
                if 'PATH' in ffmpeg_env:
                    ffmpeg_path = ffmpeg_env['PATH']
                    if ffmpeg_path and ffmpeg_path not in os.environ.get('PATH', ''):
                        os.environ['PATH'] = f"{os.environ.get('PATH', '')}:{ffmpeg_path}"
                        print(f"Added FFmpeg to PATH")
        except Exception as ffmpeg_error:
            print(f"WARNING: Failed to setup FFmpeg from Rez: {ffmpeg_error}")
            # FFmpeg 실패는 치명적이지 않음

        print("Rez environment configured successfully")
        print(f"Resolved {len(packages)} packages")
        return True

    except ImportError as e:
        print(f"ERROR: Failed to import Rez modules: {e}")
        print("       Rez may be partially installed or corrupted")
        print("       Using pip packages instead...")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error during Rez setup: {e}")
        import traceback
        traceback.print_exc()
        print("       Continuing with pip packages...")
        return False


class IOManagerApp:
    """
    IO Manager 애플리케이션 메인 클래스

    독립 실행 가능한 애플리케이션입니다.
    """

    def __init__(self, config_path=None):
        """
        Args:
            config_path: 설정 파일 경로 (기본값: config/settings.yml)
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config = None
        self.app_instance = None

        # 애플리케이션 초기화
        self._initialize()

    def _get_default_config_path(self):
        """기본 설정 파일 경로를 반환합니다."""
        app_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(app_dir, 'config', 'settings.yml')

    def _initialize(self):
        """애플리케이션을 초기화합니다."""
        # 설정 로드
        from config.app_config import AppConfig
        from python.app import AppInstance

        print(f"Loading configuration from: {self.config_path}")
        self.config = AppConfig.load(self.config_path)

        # 필수 설정 검증
        if not self.config.validate():
            raise RuntimeError("Configuration validation failed")

        # 앱 인스턴스 초기화
        self.app_instance = AppInstance.initialize(self.config, app=self)
        print("Application initialized successfully")

    def _handle_user_selection(self):
        """유저 선택 처리 (프로젝트 선택 전에 실행)"""
        from python.app import get_shotgun, AppInstance
        from python.app.utils.qt_compat import QMessageBox
        from config.app_config import AppConfig

        # 1. settings.yml에 user_id가 있는지 확인
        user_id = AppConfig.get('context.user_id', None)
        if user_id:
            print(f"Using saved user ID: {user_id}")
            return  # 이미 저장된 유저 정보 사용

        # 2. Shotgun 연결 확인
        shotgun = get_shotgun()
        if shotgun is None:
            QMessageBox.critical(
                None,
                "Shotgun Connection Failed",
                "Cannot connect to Shotgun. Please check your API credentials in settings.yml"
            )
            sys.exit(1)

        # 3. 유저 선택 다이얼로그 표시
        from python.app.ui.user_selector import show_user_selector
        selected_user = show_user_selector(shotgun)

        # 4. 취소 처리
        if selected_user is None:
            print("User selection cancelled by user")
            sys.exit(0)

        # 5. Context 업데이트 (메모리)
        AppInstance.update_user_context(selected_user)

        # 6. settings.yml에 저장
        try:
            AppConfig.save_user(selected_user)
        except Exception as e:
            import traceback
            QMessageBox.warning(
                None,
                "Save Failed",
                f"User info saved to session but could not save to settings.yml:\n{str(e)}\n\n"
                "You will need to select user again next time."
            )
            print(f"WARNING: Failed to save user to settings.yml: {e}")
            print(traceback.format_exc())

    def _handle_project_selection(self):
        """프로젝트 선택 처리"""
        from python.app import get_shotgun, AppInstance
        from python.app.utils.qt_compat import QMessageBox

        shotgun = get_shotgun()
        if shotgun is None:
            # Shotgun 연결 실패: 에러 메시지 표시 후 종료
            QMessageBox.critical(
                None,
                "Shotgun Connection Error",
                "Failed to connect to Shotgun.\n"
                "Please check your network and credentials in settings.yml"
            )
            sys.exit(1)

        from python.app.ui.project_selector import show_project_selector
        selected_project = show_project_selector(shotgun)

        if selected_project is None:
            # 사용자가 취소: 앱 종료
            print("Project selection cancelled")
            sys.exit(0)

        # Context 업데이트
        AppInstance.update_project_context(selected_project)
        print(f"Selected project: {selected_project['name']} (ID: {selected_project['id']})")

    def run(self):
        """
        애플리케이션을 실행합니다.

        Qt UI를 초기화하고 메인 다이얼로그를 표시합니다.
        """
        from python.app.utils.qt_compat import QApplication, get_qt_binding

        # QApplication 생성
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        print(f"Using Qt binding: {get_qt_binding()}")

        # 애플리케이션 정보 설정
        app.setApplicationName("IO Manager")
        app.setOrganizationName("Westworld")

        # 유저 선택 (프로젝트 선택 전에 먼저 실행)
        self._handle_user_selection()

        # 프로젝트 선택 다이얼로그 표시 (독립 실행 모드)
        self._handle_project_selection()

        # 메인 다이얼로그 표시
        try:
            from python.app import dialog
            dialog_instance = dialog.show_dialog(self)

            # 이벤트 루프 실행
            sys.exit(app.exec_())

        except Exception as e:
            import traceback
            print(f"Error running application: {e}")
            traceback.print_exc()
            sys.exit(1)


# SGTK 호환성을 위한 레거시 클래스
class StgkStarterApp:
    """
    SGTK 호환성을 위한 레거시 클래스

    기존 SGTK 환경에서도 실행 가능하도록 유지합니다.
    """

    def __init__(self):
        """SGTK Application 초기화"""
        try:
            from sgtk.platform import Application
            self._base_class = Application
        except ImportError:
            print("Warning: SGTK not available, using standalone mode")
            self._base_class = object

    def init_app(self):
        """
        SGTK 앱 초기화

        Called as the application is being initialized
        """
        try:
            # SGTK 모드에서 실행
            print("Running in SGTK mode")
            from python.app import dialog

            # 메뉴 콜백 등록
            menu_callback = lambda: dialog.show_dialog(self)
            if hasattr(self, 'engine'):
                self.engine.register_command("IO Manager", menu_callback)

        except Exception:
            import traceback
            traceback.print_exc()


def parse_arguments():
    """커맨드라인 인자를 파싱합니다."""
    parser = argparse.ArgumentParser(
        description='Westworld IO-Manager - VFX Pipeline Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 기본 설정으로 실행
  python app.py

  # 커스텀 설정 파일 사용
  python app.py --config /path/to/settings.yml

  # Rez 환경 비활성화
  python app.py --no-rez

Environment Variables:
  SHOTGUN_API_KEY       Shotgun API 키
  PROJECT_ROOT          프로젝트 루트 경로
  USER                  사용자 이름
        """
    )

    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='설정 파일 경로 (기본값: config/settings.yml)'
    )

    parser.add_argument(
        '--no-rez',
        action='store_true',
        help='Rez 환경 설정 비활성화'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='IO Manager 2.0.0'
    )

    return parser.parse_args()


def main():
    """메인 엔트리포인트"""
    print("=" * 60)
    print("Westworld IO-Manager")
    print("=" * 60)

    # 커맨드라인 인자 파싱
    args = parse_arguments()

    # Rez 환경 설정 (옵션)
    rez_configured = False

    # --no-rez 플래그 환경변수로 저장 (다른 모듈에서 참조용)
    if args.no_rez:
        os.environ['USE_REZ'] = '0'
    else:
        os.environ['USE_REZ'] = '1'

    if not args.no_rez:
        # Rez 설정을 위해 config 미리 로드 (optional)
        config_path = args.config
        if not config_path:
            app_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(app_dir, 'config', 'settings.yml')

        # 설정 파일이 있으면 로드, 없으면 기본값 사용
        config = None
        if os.path.exists(config_path):
            try:
                from config.app_config import AppConfig
                config = AppConfig.load(config_path)
                print(f"Loaded configuration from: {config_path}")

                # 설정에서 Rez 활성화 여부 확인
                if not config.get('rez.enabled', True):
                    print("Rez is disabled in configuration")
                else:
                    rez_configured = setup_rez_environment(config=config)
            except Exception as e:
                print(f"WARNING: Failed to load config for Rez setup: {e}")
                print("         Attempting Rez setup with default packages...")
                rez_configured = setup_rez_environment()
        else:
            print(f"Config file not found: {config_path}")
            print("Using default Rez packages...")
            rez_configured = setup_rez_environment()

        if rez_configured:
            print("✓ Rez environment ready")
        else:
            print("✗ Rez environment not available, using pip packages")
    else:
        print("Rez environment disabled by --no-rez flag")

    print("-" * 60)

    # 애플리케이션 실행
    try:
        app = IOManagerApp(config_path=args.config)
        app.run()
    except Exception as e:
        import traceback
        print(f"\nFATAL ERROR: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
