"""
애플리케이션 설정 관리 모듈

이 모듈은 애플리케이션의 모든 설정을 관리합니다.
YAML 파일에서 설정을 로드하고, 환경변수를 처리하며,
Shotgun API 인스턴스를 생성합니다.
"""

import os
import re
import yaml
from typing import Any, Dict, Optional


class AppConfig:
    """
    애플리케이션 설정 관리 클래스 (싱글톤)

    YAML 파일에서 설정을 로드하고 환경변수를 처리합니다.
    """

    _instance = None
    _config_data = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppConfig, cls).__new__(cls)
        return cls._instance

    @classmethod
    def load(cls, config_path: str) -> 'AppConfig':
        """
        설정 파일을 로드합니다.

        Args:
            config_path: YAML 설정 파일 경로

        Returns:
            AppConfig 인스턴스

        Raises:
            FileNotFoundError: 설정 파일이 존재하지 않을 때
            yaml.YAMLError: YAML 파싱 오류
        """
        instance = cls()

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            cls._config_data = yaml.safe_load(f)

        # 환경변수 치환
        cls._config_data = cls._resolve_env_vars(cls._config_data)

        return instance

    @classmethod
    def _resolve_env_vars(cls, data: Any) -> Any:
        """
        설정 값에서 환경변수를 재귀적으로 치환합니다.

        ${ENV_VAR} 또는 $ENV_VAR 형식의 환경변수를 실제 값으로 치환합니다.

        Args:
            data: 설정 데이터 (dict, list, str 등)

        Returns:
            환경변수가 치환된 데이터
        """
        if isinstance(data, dict):
            return {key: cls._resolve_env_vars(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [cls._resolve_env_vars(item) for item in data]
        elif isinstance(data, str):
            # ${VAR} 또는 $VAR 형식의 환경변수 치환
            def replace_env(match):
                var_name = match.group(1) or match.group(2)
                return os.environ.get(var_name, match.group(0))

            pattern = r'\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)'
            return re.sub(pattern, replace_env, data)
        else:
            return data

    @classmethod
    def get(cls, key: str = None, default: Any = None) -> Any:
        """
        설정 값을 가져옵니다.

        중첩된 키는 점(.)으로 구분합니다.
        예: 'shotgun.base_url'

        Args:
            key: 설정 키 (None이면 전체 설정 반환)
            default: 키가 없을 때 반환할 기본값

        Returns:
            설정 값
        """
        if cls._config_data is None:
            raise RuntimeError("Config not loaded. Call AppConfig.load() first.")

        if key is None:
            return cls._config_data

        # 점으로 구분된 키 처리
        keys = key.split('.')
        value = cls._config_data

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    @classmethod
    def get_shotgun_url(cls) -> str:
        """Shotgun URL을 반환합니다."""
        return cls.get('shotgun.base_url', '')

    @classmethod
    def get_shotgun_script_name(cls) -> str:
        """Shotgun 스크립트 이름을 반환합니다."""
        return cls.get('shotgun.script_name', '')

    @classmethod
    def get_shotgun_api_key(cls) -> str:
        """Shotgun API 키를 반환합니다."""
        return cls.get('shotgun.script_key', '')

    @classmethod
    def get_project_path(cls) -> str:
        """프로젝트 경로를 반환합니다."""
        return cls.get('project.path', '')

    @classmethod
    def get_project_name(cls) -> str:
        """프로젝트 이름을 반환합니다."""
        return cls.get('project.name', '')

    @classmethod
    def get_project_id(cls) -> Optional[int]:
        """프로젝트 ID를 반환합니다."""
        return cls.get('context.project_id')

    @classmethod
    def get_user(cls) -> str:
        """사용자 이름을 반환합니다."""
        return cls.get('context.user', os.environ.get('USER', 'unknown'))

    @classmethod
    def get_context(cls) -> Dict[str, Any]:
        """
        컨텍스트 정보를 딕셔너리로 반환합니다.

        Returns:
            컨텍스트 딕셔너리 (project_id, user 등)
        """
        return {
            'project_id': cls.get_project_id(),
            'project_name': cls.get_project_name(),
            'project_path': cls.get_project_path(),
            'user': cls.get_user(),
        }

    @classmethod
    def save_user(cls, user_dict: Dict[str, Any]) -> None:
        """
        유저 정보를 settings.yml에 저장합니다.

        Args:
            user_dict: Shotgun 유저 딕셔너리
                      {'id': 456, 'name': '홍길동', 'email': 'user@example.com'}

        Raises:
            FileNotFoundError: 설정 파일이 존재하지 않을 때
            IOError: 파일 쓰기 실패 시
            yaml.YAMLError: YAML 포맷 에러 시
        """
        from pathlib import Path

        # settings.yml 경로
        config_path = Path(__file__).parent / 'settings.yml'

        # 파일 읽기
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        # context 섹션 업데이트
        if 'context' not in config_data:
            config_data['context'] = {}

        config_data['context']['user_id'] = user_dict['id']
        config_data['context']['user_name'] = user_dict['name']
        if 'email' in user_dict:
            config_data['context']['user_email'] = user_dict['email']

        # 임시 파일에 쓰기 (원자적 업데이트)
        temp_path = config_path.with_suffix('.yml.tmp')
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(config_data, f,
                              default_flow_style=False,
                              allow_unicode=True,
                              sort_keys=False)

            # 원본 파일 교체
            temp_path.replace(config_path)

            # 메모리 캐시 업데이트
            cls._config_data = cls._resolve_env_vars(config_data)

            print(f"User info saved to settings.yml: {user_dict['name']} (ID: {user_dict['id']})")

        except Exception as e:
            # 임시 파일 정리
            if temp_path.exists():
                temp_path.unlink()
            raise IOError(f"Failed to save config: {str(e)}")

    @classmethod
    def validate(cls) -> bool:
        """
        필수 설정 값이 모두 존재하는지 검증합니다.

        Returns:
            검증 성공 여부
        """
        required_keys = [
            'shotgun.base_url',
            'project.path',
            'project.name',
        ]

        for key in required_keys:
            if not cls.get(key):
                print(f"Missing required config: {key}")
                return False

        return True


class Context:
    """
    SGTK Context를 대체하는 간단한 컨텍스트 클래스

    프로젝트, 사용자 등의 컨텍스트 정보를 담습니다.
    """

    def __init__(self, project=None, user=None, entity=None, step=None, task=None):
        """
        Args:
            project: 프로젝트 정보 (dict)
            user: 사용자 정보 (dict)
            entity: 엔티티 정보 (dict) - Shot, Sequence 등
            step: 파이프라인 스텝 정보 (dict)
            task: 태스크 정보 (dict)
        """
        self.project = project
        self.user = user
        self.entity = entity
        self.step = step
        self.task = task

    @classmethod
    def from_config(cls) -> 'Context':
        """
        AppConfig에서 컨텍스트를 생성합니다.

        Returns:
            Context 인스턴스
        """
        project_id = AppConfig.get_project_id()

        # User - ID 우선, 없으면 이름만
        user_id = AppConfig.get('context.user_id', None)
        user_name = AppConfig.get('context.user_name', None) or AppConfig.get_user()

        # ID가 있으면 완전한 엔티티 딕셔너리 생성
        if user_id:
            user = {
                'type': 'HumanUser',
                'id': user_id,
                'name': user_name
            }
        else:
            # ID 없으면 이름만 (하위 호환성)
            user = {
                'type': 'HumanUser',
                'name': user_name
            }

        return cls(
            project={
                'type': 'Project',
                'id': project_id,
                'name': AppConfig.get_project_name()
            },
            user=user
        )

    def __repr__(self):
        return f"Context(project={self.project}, user={self.user})"
