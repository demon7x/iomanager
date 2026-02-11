"""
썸네일 다운로드 및 플레이스홀더 생성 유틸리티

Shotgun 이미지 URL에서 썸네일을 다운로드하고,
이미지가 없을 경우 플레이스홀더를 생성합니다.
"""

from typing import Optional

from .qt_compat import QPixmap, QImage, Qt, QColor, QPainter, QFont


def download_thumbnail(image_url, timeout: int = 5) -> Optional[QPixmap]:
    """
    Shotgun 이미지 URL에서 썸네일을 다운로드합니다.

    Args:
        image_url: Shotgun 이미지 URL (문자열 또는 딕셔너리)
        timeout: 다운로드 타임아웃 (초)

    Returns:
        QPixmap 썸네일 또는 None (실패 시)
    """
    try:
        # image_url이 딕셔너리면 실제 URL 추출
        if isinstance(image_url, dict):
            # Shotgun API는 {'url': 'http://...'} 형태로 반환할 수 있음
            url = image_url.get('url')
            if not url:
                return None
        elif isinstance(image_url, str):
            url = image_url
        else:
            return None

        # URL이 비어있으면 None 반환
        if not url:
            return None

        # requests 라이브러리로 다운로드
        import requests
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()

        # QImage로 변환
        image = QImage.fromData(response.content)
        if image.isNull():
            return None

        # QPixmap으로 변환 및 크기 조정
        pixmap = QPixmap.fromImage(image)
        pixmap = pixmap.scaled(240, 144, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        return pixmap

    except ImportError:
        print("Warning: requests library not installed. Cannot download thumbnails.")
        print("Install with: pip install requests")
        return None
    except Exception as e:
        print(f"Error downloading thumbnail: {e}")
        return None


def create_placeholder(project_name: str, width: int = 240, height: int = 144) -> QPixmap:
    """
    프로젝트 썸네일 플레이스홀더를 생성합니다.

    Args:
        project_name: 프로젝트 이름
        width: 플레이스홀더 너비
        height: 플레이스홀더 높이

    Returns:
        QPixmap 플레이스홀더
    """
    # 빈 픽스맵 생성
    pixmap = QPixmap(width, height)

    # 배경색 설정 (짙은 회색)
    pixmap.fill(QColor(60, 60, 60))

    # QPainter로 텍스트 그리기
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    # 테두리 그리기
    painter.setPen(QColor(100, 100, 100))
    painter.drawRect(0, 0, width - 1, height - 1)

    # 프로젝트 이니셜 추출 (최대 3글자)
    initials = _get_initials(project_name)

    # 텍스트 설정
    painter.setPen(QColor(180, 180, 180))
    font = QFont()
    font.setPixelSize(48)
    font.setBold(True)
    painter.setFont(font)

    # 텍스트 중앙 정렬
    painter.drawText(pixmap.rect(), Qt.AlignCenter, initials)

    painter.end()

    return pixmap


def _get_initials(project_name: str) -> str:
    """
    프로젝트 이름에서 이니셜을 추출합니다.

    Args:
        project_name: 프로젝트 이름

    Returns:
        이니셜 문자열 (최대 3글자)

    Examples:
        "Westworld" -> "W"
        "The Matrix" -> "TM"
        "Star Wars Episode IV" -> "SWE"
    """
    if not project_name:
        return "?"

    # 공백으로 단어 분리
    words = project_name.split()

    if not words:
        return "?"

    # 각 단어의 첫 글자 추출
    initials = ''.join([word[0].upper() for word in words if word])

    # 최대 3글자로 제한
    if len(initials) > 3:
        initials = initials[:3]

    return initials or "?"
