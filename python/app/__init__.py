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
App 패키지

IO Manager 애플리케이션의 메인 패키지입니다.
"""

import os
import sys
from typing import Optional

# 현재는 SGTK 의존성 제거를 위해 주석 처리
# from . import dialog


class AppInstance:
    """
    글로벌 애플리케이션 인스턴스 관리 (싱글톤)

    이 클래스는 애플리케이션의 전역 상태를 관리합니다:
    - Shotgun API 인스턴스
    - 설정 객체
    - 컨텍스트 정보

    sgtk.platform.current_bundle()을 대체합니다.
    """

    _instance = None
    _shotgun = None
    _config = None
    _context = None
    _app = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppInstance, cls).__new__(cls)
        return cls._instance

    @classmethod
    def initialize(cls, config, app=None):
        """
        앱 인스턴스를 초기화합니다.

        Args:
            config: AppConfig 인스턴스
            app: 메인 애플리케이션 객체 (선택사항)
        """
        instance = cls()
        cls._config = config
        cls._app = app

        # Shotgun API 초기화
        cls._initialize_shotgun()

        # 컨텍스트 초기화
        from config.app_config import Context
        cls._context = Context.from_config()

        return instance

    @classmethod
    def _initialize_shotgun(cls):
        """Shotgun API를 초기화합니다."""
        try:
            import shotgun_api3

            from config.app_config import AppConfig

            base_url = AppConfig.get_shotgun_url()
            script_name = AppConfig.get_shotgun_script_name()
            api_key = AppConfig.get_shotgun_api_key()

            if not base_url:
                print("Warning: Shotgun base_url not configured")
                return

            if not script_name or not api_key:
                print("Warning: Shotgun credentials not configured")
                print("Set SHOTGUN_API_KEY environment variable")
                return

            cls._shotgun = shotgun_api3.Shotgun(
                base_url,
                script_name=script_name,
                api_key=api_key
            )

            print(f"Shotgun API initialized: {base_url}")

        except ImportError:
            print("Warning: shotgun_api3 not installed")
            print("Install with: pip install shotgun-api3")
        except Exception as e:
            print(f"Error initializing Shotgun API: {e}")

    @classmethod
    def get(cls) -> 'AppInstance':
        """
        현재 앱 인스턴스를 반환합니다.

        sgtk.platform.current_bundle()을 대체합니다.

        Returns:
            AppInstance 인스턴스

        Raises:
            RuntimeError: 앱 인스턴스가 초기화되지 않았을 때
        """
        if cls._instance is None:
            raise RuntimeError(
                "AppInstance not initialized. "
                "Call AppInstance.initialize() first."
            )
        return cls._instance

    @classmethod
    def get_shotgun(cls):
        """
        Shotgun API 인스턴스를 반환합니다.

        self._app.shotgun 또는 self._app.sgtk.shotgun을 대체합니다.

        Returns:
            shotgun_api3.Shotgun 인스턴스
        """
        return cls._shotgun

    @classmethod
    def get_context(cls):
        """
        컨텍스트를 반환합니다.

        self._app.context를 대체합니다.

        Returns:
            Context 인스턴스
        """
        return cls._context

    @classmethod
    def update_project_context(cls, project_dict):
        """
        런타임에 프로젝트 컨텍스트를 업데이트합니다.

        Args:
            project_dict: Shotgun 프로젝트 딕셔너리
                         {'type': 'Project', 'id': 123, 'name': 'ProjectName'}
        """
        if cls._context is None:
            from config.app_config import Context
            cls._context = Context()

        # 프로젝트 정보 업데이트
        cls._context.project = {
            'type': 'Project',
            'id': project_dict['id'],
            'name': project_dict.get('name', project_dict.get('code', 'Unknown'))
        }

        print(f"Context updated: Project ID={project_dict['id']}, Name={project_dict['name']}")

    @classmethod
    def update_user_context(cls, user_dict):
        """
        런타임에 유저 컨텍스트를 업데이트합니다.

        Args:
            user_dict: Shotgun 유저 딕셔너리
                      {'type': 'HumanUser', 'id': 456, 'name': '홍길동', 'email': '...'}
        """
        if cls._context is None:
            from config.app_config import Context
            cls._context = Context()

        cls._context.user = {
            'type': 'HumanUser',
            'id': user_dict['id'],
            'name': user_dict['name']
        }

        print(f"Context updated: User ID={user_dict['id']}, Name={user_dict['name']}")

    @classmethod
    def get_config(cls):
        """
        설정 객체를 반환합니다.

        Returns:
            AppConfig 인스턴스
        """
        return cls._config

    @property
    def shotgun(self):
        """Shotgun API 인스턴스 (프로퍼티)"""
        return self.get_shotgun()

    @property
    def context(self):
        """컨텍스트 (프로퍼티)"""
        return self.get_context()

    @property
    def sgtk(self):
        """
        SGTK 호환성을 위한 가짜 객체

        기존 코드: self._app.sgtk.shotgun, self._app.sgtk.project_path
        """
        return _SGTKCompat()


class _SGTKCompat:
    """
    SGTK API 호환성을 위한 가짜 클래스

    기존 코드에서 self._app.sgtk.xxx 형태로 접근하는 것을 지원합니다.
    """

    @property
    def shotgun(self):
        """Shotgun API 인스턴스"""
        return AppInstance.get_shotgun()

    @property
    def project_path(self):
        """프로젝트 경로"""
        from config.app_config import AppConfig
        return AppConfig.get_project_path()

    @property
    def tank(self):
        """Tank (구 SGTK) 호환성"""
        return self


# 편의를 위한 모듈 레벨 함수
def get_app_instance():
    """
    현재 앱 인스턴스를 반환합니다.

    Returns:
        AppInstance 인스턴스
    """
    return AppInstance.get()


def get_shotgun():
    """
    Shotgun API 인스턴스를 반환합니다.

    Returns:
        shotgun_api3.Shotgun 인스턴스
    """
    return AppInstance.get_shotgun()


def get_context():
    """
    컨텍스트를 반환합니다.

    Returns:
        Context 인스턴스
    """
    return AppInstance.get_context()


# Export
__all__ = [
    'AppInstance',
    'get_app_instance',
    'get_shotgun',
    'get_context',
]
